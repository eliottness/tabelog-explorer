"""Core scraping functionality for Tabelog."""

import re
from dataclasses import dataclass
from urllib.parse import quote, urljoin

import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}

BASE_URL = "https://tabelog.com"


@dataclass
class Restaurant:
    """Restaurant basic info."""
    id: str
    name: str
    rating: str
    area: str
    cuisine: str
    url: str


@dataclass
class RestaurantDetail:
    """Detailed restaurant info."""
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


def _get_soup(url: str) -> BeautifulSoup:
    """Fetch URL and return BeautifulSoup object."""
    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return BeautifulSoup(response.text, "lxml")


def _extract_rating_from_class(classes: list[str]) -> str:
    """Extract rating from CSS class like c-rating-v3--val35 = 3.5."""
    for cls in classes:
        match = re.search(r"c-rating-v3--val(\d+)", cls)
        if match:
            val = int(match.group(1))
            return f"{val / 10:.1f}"
    return "N/A"


def id_to_url(restaurant_id: str) -> str:
    """Convert a restaurant ID to its Tabelog URL.

    IDs are like '13002251' - we need to search for it to get the full URL.
    For now, we'll construct a likely URL pattern.
    """
    # Tabelog URLs follow pattern: /prefecture/area/subarea/ID/
    # We can use the search to find the actual URL, or try common patterns
    # For Tokyo restaurants starting with 13, the pattern is predictable
    if restaurant_id.startswith("13"):
        return f"{BASE_URL}/tokyo/A1301/A130101/{restaurant_id}/"
    # For other regions, we'd need to search - for now return a search URL
    return f"{BASE_URL}/rstLst/?vs=1&sw={restaurant_id}"


def search_restaurants(query: str, area: str | None = None) -> list[Restaurant]:
    """Search for restaurants by keyword."""
    # Build search URL
    encoded_query = quote(query)
    if area:
        # Area format: tokyo/ginza -> /tokyo/A1301/A130101/rstLst/
        search_url = f"{BASE_URL}/{area}/rstLst/?vs=1&sw={encoded_query}"
    else:
        search_url = f"{BASE_URL}/rstLst/?vs=1&sw={encoded_query}"

    soup = _get_soup(search_url)
    restaurants = []

    # Find restaurant list items
    for item in soup.select(".list-rst"):
        # Get restaurant link and ID
        link_elem = item.select_one(".list-rst__rst-name-target")
        if not link_elem:
            continue

        url = link_elem.get("href", "")
        # Extract ID from URL (last numeric segment)
        id_match = re.search(r"/(\d+)/?$", url)
        rst_id = id_match.group(1) if id_match else ""

        name = link_elem.get_text(strip=True)

        # Get rating
        rating_elem = item.select_one(".c-rating__val")
        rating = rating_elem.get_text(strip=True) if rating_elem else "N/A"

        # Get area
        area_elem = item.select_one(".list-rst__area-genre")
        area_text = ""
        cuisine = ""
        if area_elem:
            parts = area_elem.get_text(strip=True).split("/")
            area_text = parts[0].strip() if parts else ""
            cuisine = parts[1].strip() if len(parts) > 1 else ""

        restaurants.append(Restaurant(
            id=rst_id,
            name=name,
            rating=rating,
            area=area_text,
            cuisine=cuisine,
            url=url,
        ))

    return restaurants


def get_restaurant_info(restaurant_id: str) -> RestaurantDetail | None:
    """Get detailed info for a restaurant."""
    # First, try to construct URL directly for Tokyo restaurants
    if restaurant_id.startswith("13"):
        # Try common Tokyo area patterns
        for area_code in ["A1301/A130101", "A1302/A130201", "A1303/A130301", "A1304/A130401"]:
            url = f"{BASE_URL}/tokyo/{area_code}/{restaurant_id}/"
            try:
                soup = _get_soup(url)
                # Check if we got a valid restaurant page
                name_elem = soup.select_one("h2.display-name a")
                if name_elem:
                    break
            except requests.RequestException:
                continue
        else:
            return None
    else:
        # For non-Tokyo, we'd need to search first
        # For now, try a direct search
        results = search_restaurants(restaurant_id)
        if results:
            url = results[0].url
            soup = _get_soup(url)
        else:
            return None

    # Parse restaurant details
    name_elem = soup.select_one("h2.display-name a")
    if not name_elem:
        name_elem = soup.select_one("h2.display-name")
    name = name_elem.get_text(strip=True) if name_elem else "Unknown"

    # Rating
    rating_elem = soup.select_one(".rdheader-rating__score-val-dtl")
    if not rating_elem:
        rating_elem = soup.select_one(".rdheader-rating__score-val")
    rating = rating_elem.get_text(strip=True) if rating_elem else "N/A"

    # Address
    address_elem = soup.select_one(".rstinfo-table__address")
    address = address_elem.get_text(strip=True) if address_elem else ""

    # Cuisine/genre
    genre_elem = soup.select_one(".rdheader-subinfo__genre")
    cuisine = genre_elem.get_text(strip=True) if genre_elem else ""

    # Price (lunch/dinner)
    price_lunch = ""
    price_dinner = ""
    budget_elems = soup.select(".rdheader-budget__price")
    for elem in budget_elems:
        text = elem.get_text(strip=True)
        label = elem.find_previous_sibling()
        if label and "昼" in label.get_text():
            price_lunch = text
        elif label and "夜" in label.get_text():
            price_dinner = text

    # Hours
    hours_elem = soup.select_one(".rstinfo-table__business-hours")
    hours = hours_elem.get_text(strip=True) if hours_elem else ""

    return RestaurantDetail(
        id=restaurant_id,
        name=name,
        rating=rating,
        address=address,
        cuisine=cuisine,
        price_lunch=price_lunch,
        price_dinner=price_dinner,
        hours=hours,
        url=url,
    )


def get_reviews(restaurant_id: str | None = None, url: str | None = None) -> tuple[str, str, list[Review]]:
    """Fetch reviews for a restaurant. Returns (name, rating, reviews)."""
    if url:
        # Use provided URL
        if "/dtlrvwlst/" not in url:
            url = url.rstrip("/") + "/dtlrvwlst/"
    elif restaurant_id:
        # Build URL from ID
        base_url = id_to_url(restaurant_id)
        url = base_url.rstrip("/") + "/dtlrvwlst/"
    else:
        raise ValueError("Must provide either restaurant_id or url")

    soup = _get_soup(url)

    # Get restaurant name
    name_elem = soup.select_one("h2.display-name a")
    if not name_elem:
        name_elem = soup.select_one("h2.display-name")
    restaurant_name = name_elem.get_text(strip=True) if name_elem else "Unknown Restaurant"

    # Get overall rating
    rating_elem = soup.select_one(".rdheader-rating__score-val-dtl")
    if not rating_elem:
        rating_elem = soup.select_one(".rdheader-rating__score-val")
    overall_rating = rating_elem.get_text(strip=True) if rating_elem else "N/A"

    # Parse reviews
    reviews = []
    for review_elem in soup.select(".rvw-item"):
        # Rating from class
        review_rating = "N/A"
        rating_p = review_elem.select_one(".rvw-item__ratings-total")
        if rating_p:
            classes = rating_p.get("class", [])
            review_rating = _extract_rating_from_class(classes)

        # Title
        title_elem = review_elem.select_one(".rvw-item__title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Body
        body_elem = review_elem.select_one(".rvw-item__rvw-comment")
        if body_elem:
            for a in body_elem.select("a"):
                a.decompose()
            body = body_elem.get_text(strip=True)
        else:
            body = ""

        # Visit date
        date_elem = review_elem.select_one(".rvw-item__visit-date")
        visit_date = date_elem.get_text(strip=True) if date_elem else ""

        reviews.append(Review(
            rating=review_rating,
            title=title,
            body=body,
            visit_date=visit_date,
        ))

    return restaurant_name, overall_rating, reviews
