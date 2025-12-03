"""Tabelog API client."""

from urllib.parse import quote

from ._http import BASE_URL, fetch_soup
from ._parse import parse_areas, parse_restaurant_detail, parse_reviews, parse_search_results
from .genres import GENRES, get_genre_url, list_genres
from .models import Area, Restaurant, RestaurantDetail, Review

# Common filter URL patterns
FILTERS = {
    "private_room": "cond07-00-00",
    "non_smoking": "cond13-00-00",
    "lunch": "lunch",
    "reservable": "cond11-00-00",
    "all_you_can_drink": "cond05-00-00",
    "all_you_can_eat": "cond02-00-00",
    "card_ok": "cond20-00-00",
    "parking": "cond19-00-00",
    "kids_ok": "cond10-00-00",
    "sunday_open": "cond14-00-00",
    "solo": "cond04-00-02",
    "date": "cond04-00-03",
    "counter": "cond03-10-00",
    "tatami": "cond03-02-00",
}


class TabelogClient:
    """Client for interacting with Tabelog."""

    def search(
        self,
        query: str | None = None,
        area: str | None = None,
        genre: str | None = None,
        filters: list[str] | None = None,
    ) -> list[Restaurant]:
        """Search for restaurants.

        Args:
            query: Search keyword
            area: Area code (e.g., 'tokyo', 'tokyo/A1301')
            genre: Genre slug (e.g., 'ramen', 'sushi')
            filters: List of filter names (e.g., ['private_room', 'non_smoking'])
        """
        # Build base URL
        if area:
            base = f"{BASE_URL}/{area}"
        else:
            base = BASE_URL

        # Build path: rstLst/[filter]/[genre]/
        # Note: Only ONE filter can be in the path. Additional filters go in query params.
        url = f"{base}/rstLst/"
        query_params = []

        # Add first filter to path, rest to query params
        if filters:
            valid_filters = [f for f in filters if f in FILTERS]
            if valid_filters:
                # First filter goes in path
                url = url.rstrip("/") + f"/{FILTERS[valid_filters[0]]}/"
                # Additional filters go in query params
                for f in valid_filters[1:]:
                    query_params.append(f"{FILTERS[f]}=1")

        # Add genre after filter
        if genre:
            if genre not in GENRES:
                raise ValueError(f"Unknown genre: {genre}. Use list_genres() to see available options.")
            url = url.rstrip("/") + f"/{genre}/"

        # Build query string
        if query:
            query_params.insert(0, f"vs=1&sw={quote(query)}")

        if query_params:
            url = f"{url}?{'&'.join(query_params)}"

        soup = fetch_soup(url)
        return parse_search_results(soup)

    def get_info(self, restaurant_id: str) -> RestaurantDetail | None:
        """Get detailed info for a restaurant by ID."""
        # Try common Tokyo area patterns for IDs starting with 13
        if restaurant_id.startswith("13"):
            for area_code in ["A1301/A130101", "A1302/A130201", "A1303/A130301", "A1304/A130401"]:
                url = f"{BASE_URL}/tokyo/{area_code}/{restaurant_id}/"
                try:
                    soup = fetch_soup(url)
                    result = parse_restaurant_detail(soup, restaurant_id, url)
                    if result:
                        return result
                except Exception:
                    continue
            return None

        # For non-Tokyo, search first
        results = self.search(query=restaurant_id)
        if results:
            url = results[0].url
            soup = fetch_soup(url)
            return parse_restaurant_detail(soup, restaurant_id, url)
        return None

    def get_reviews(
        self,
        restaurant_id: str | None = None,
        url: str | None = None,
    ) -> tuple[str, str, list[Review]]:
        """Fetch reviews for a restaurant. Returns (name, rating, reviews)."""
        if url:
            if "/dtlrvwlst/" not in url:
                url = url.rstrip("/") + "/dtlrvwlst/"
        elif restaurant_id:
            info = self.get_info(restaurant_id)
            if info:
                url = info.url.rstrip("/") + "/dtlrvwlst/"
            else:
                raise ValueError(f"Restaurant {restaurant_id} not found")
        else:
            raise ValueError("Must provide either restaurant_id or url")

        soup = fetch_soup(url)
        return parse_reviews(soup)

    def get_areas(self, region: str) -> list[Area]:
        """Fetch areas for a region dynamically."""
        url = f"{BASE_URL}/{region}/"
        soup = fetch_soup(url)
        return parse_areas(soup)

    def list_genres(self) -> list[tuple[str, str, str]]:
        """List all available genres. Returns [(slug, japanese, english), ...]."""
        return list_genres()
