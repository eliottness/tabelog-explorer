"""HTTP utilities for Tabelog scraping."""

import asyncio
import time
from typing import NamedTuple

import aiohttp
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://tabelog.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}

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


def fetch_soup(url: str, use_cache: bool = True) -> BeautifulSoup:
    """Fetch URL and return BeautifulSoup object."""
    # Check cache first
    if use_cache:
        cached = _get_cached(url)
        if cached:
            return BeautifulSoup(cached, "lxml")

    session = _get_session()
    response = session.get(url, timeout=30)
    response.raise_for_status()

    # Cache the response
    if use_cache:
        _set_cache(url, response.text)

    return BeautifulSoup(response.text, "lxml")


async def fetch_soup_async(
    url: str, session: aiohttp.ClientSession, use_cache: bool = True
) -> BeautifulSoup:
    """Fetch URL asynchronously and return BeautifulSoup object."""
    # Check cache first
    if use_cache:
        cached = _get_cached(url)
        if cached:
            return BeautifulSoup(cached, "lxml")

    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
        response.raise_for_status()
        text = await response.text()

        # Cache the response
        if use_cache:
            _set_cache(url, text)

        return BeautifulSoup(text, "lxml")


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
    return asyncio.run(fetch_soups_async(urls))
