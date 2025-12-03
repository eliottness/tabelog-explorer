"""Data models for Tabelog API."""

from dataclasses import dataclass


@dataclass
class Restaurant:
    """Restaurant basic info from search results."""
    id: str
    name: str
    rating: str
    area: str
    cuisine: str
    url: str


@dataclass
class RestaurantDetail:
    """Detailed restaurant info from restaurant page."""
    id: str
    name: str
    rating: str
    address: str
    cuisine: str
    price_lunch: str
    price_dinner: str
    hours: str
    url: str


@dataclass
class Review:
    """A single review."""
    rating: str
    title: str
    body: str
    visit_date: str


@dataclass
class Area:
    """Area/region info."""
    code: str
    name: str
    parent_code: str | None = None
