"""HTTP utilities for Tabelog scraping."""

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
