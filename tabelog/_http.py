"""HTTP utilities for Tabelog scraping."""

import asyncio

import aiohttp
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://tabelog.com"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}

_session: requests.Session | None = None


def _get_session() -> requests.Session:
    """Get or create a session with proper headers."""
    global _session
    if _session is None:
        _session = requests.Session()
        _session.headers.update(HEADERS)
    return _session


def fetch_soup(url: str) -> BeautifulSoup:
    """Fetch URL and return BeautifulSoup object."""
    session = _get_session()
    response = session.get(url, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


async def fetch_soup_async(url: str, session: aiohttp.ClientSession) -> BeautifulSoup:
    """Fetch URL asynchronously and return BeautifulSoup object."""
    async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
        response.raise_for_status()
        text = await response.text()
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
