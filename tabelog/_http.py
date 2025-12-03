"""HTTP utilities for Tabelog scraping."""

import asyncio
import logging
import random
import time
from typing import NamedTuple

import aiohttp
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://tabelog.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}

# Retry configuration
MAX_RETRIES = 3
BASE_DELAY = 1.0  # seconds
MAX_DELAY = 10.0  # seconds
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

_session: requests.Session | None = None

# Simple cache with TTL
CACHE_TTL = 300  # 5 minutes


class CacheEntry(NamedTuple):
    html: str
    timestamp: float


_cache: dict[str, CacheEntry] = {}


def _get_cached(url: str) -> str | None:
    """Get cached HTML if still valid."""
    if url in _cache:
        entry = _cache[url]
        if time.time() - entry.timestamp < CACHE_TTL:
            return entry.html
        del _cache[url]
    return None


def _set_cache(url: str, html: str) -> None:
    """Cache HTML content."""
    # Limit cache size to prevent memory issues
    if len(_cache) > 100:
        # Remove oldest entries
        sorted_entries = sorted(_cache.items(), key=lambda x: x[1].timestamp)
        for key, _ in sorted_entries[:50]:
            del _cache[key]
    _cache[url] = CacheEntry(html=html, timestamp=time.time())


def clear_cache() -> None:
    """Clear the HTTP cache."""
    _cache.clear()


def _get_session() -> requests.Session:
    """Get or create a session with proper headers."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
    return _session


def _calculate_backoff(attempt: int) -> float:
    """Calculate exponential backoff with jitter."""
    delay = min(BASE_DELAY * (2 ** attempt), MAX_DELAY)
    # Add jitter (±25%)
    jitter = delay * 0.25 * (2 * random.random() - 1)
    return delay + jitter


def fetch_soup(url: str, use_cache: bool = True) -> BeautifulSoup:
    """Fetch URL and return BeautifulSoup object with retry logic."""
    # Check cache first
    if use_cache:
        cached = _get_cached(url)
        if cached:
            return BeautifulSoup(cached, "lxml")

    session = _get_session()
    last_exception: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            response = session.get(url, timeout=30)

            # Check for retryable status codes
            if response.status_code in RETRYABLE_STATUS_CODES:
                delay = _calculate_backoff(attempt)
                logger.warning(
                    f"Request to {url} returned {response.status_code}, "
                    f"retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                time.sleep(delay)
                continue

            response.raise_for_status()

            # Cache the response
            if use_cache:
                _set_cache(url, response.text)

            return BeautifulSoup(response.text, "lxml")

        except requests.exceptions.RequestException as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                delay = _calculate_backoff(attempt)
                logger.warning(
                    f"Request to {url} failed: {e}, "
                    f"retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                time.sleep(delay)
            else:
                logger.error(f"Request to {url} failed after {MAX_RETRIES} attempts: {e}")

    # If we get here, all retries failed
    raise last_exception or requests.exceptions.RequestException(
        f"Failed to fetch {url} after {MAX_RETRIES} attempts"
    )


async def fetch_soup_async(
    url: str, session: aiohttp.ClientSession, use_cache: bool = True
) -> BeautifulSoup:
    """Fetch URL asynchronously and return BeautifulSoup object with retry logic."""
    # Check cache first
    if use_cache:
        cached = _get_cached(url)
        if cached:
            return BeautifulSoup(cached, "lxml")

    last_exception: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            async with session.get(
                url, timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                # Check for retryable status codes
                if response.status in RETRYABLE_STATUS_CODES:
                    delay = _calculate_backoff(attempt)
                    logger.warning(
                        f"Async request to {url} returned {response.status}, "
                        f"retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
                    )
                    await asyncio.sleep(delay)
                    continue

                response.raise_for_status()
                text = await response.text()

                # Cache the response
                if use_cache:
                    _set_cache(url, text)

                return BeautifulSoup(text, "lxml")

        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            last_exception = e
            if attempt < MAX_RETRIES - 1:
                delay = _calculate_backoff(attempt)
                logger.warning(
                    f"Async request to {url} failed: {e}, "
                    f"retrying in {delay:.1f}s (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(delay)
            else:
                logger.error(
                    f"Async request to {url} failed after {MAX_RETRIES} attempts: {e}"
                )

    # If we get here, all retries failed
    raise last_exception or aiohttp.ClientError(
        f"Failed to fetch {url} after {MAX_RETRIES} attempts"
    )


async def fetch_soups_async(urls: list[str]) -> list[BeautifulSoup]:
    """Fetch multiple URLs in parallel and return list of BeautifulSoup objects."""
    async with aiohttp.ClientSession(headers=HEADERS) as session:
        tasks = [fetch_soup_async(url, session) for url in urls]
        return await asyncio.gather(*tasks)


def fetch_soups_parallel(urls: list[str]) -> list[BeautifulSoup]:
    """Fetch multiple URLs in parallel (sync wrapper for async fetch)."""
    if not urls:
        return []
    if len(urls) == 1:
        return [fetch_soup(urls[0])]

    # Check if we're already in an async context
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # No running loop - safe to use asyncio.run()
        return asyncio.run(fetch_soups_async(urls))

    # Already in an async context - run in a separate thread to avoid
    # "asyncio.run() cannot be called from a running event loop" error
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, fetch_soups_async(urls))
        return future.result()
