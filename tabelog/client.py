"""Tabelog API client."""

from urllib.parse import quote

from ._http import BASE_URL, fetch_soup, fetch_soups_parallel
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

# Sort options
SORT_OPTIONS = {
    "trend": None,  # Default - no params needed
    "rating": "SrtT=rt&Srt=D&sort_mode=1",  # Highest rating
    "reviews": "SrtT=rvcn&Srt=D",  # Most reviews
}


class TabelogClient:
    """Client for interacting with Tabelog."""

    def search(
        self,
        query: str | None = None,
        area: str | None = None,
        genre: str | None = None,
        filters: list[str] | None = None,
        sort: str | None = None,
    ) -> list[Restaurant]:
        """Search for restaurants.

        Args:
            query: Search keyword
            area: Area code (e.g., 'tokyo', 'tokyo/A1301')
            genre: Genre slug (e.g., 'ramen', 'sushi')
            filters: List of filter names (e.g., ['private_room', 'non_smoking'])
            sort: Sort order ('trend', 'rating', 'reviews')
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

        # Add sort params
        if sort and sort in SORT_OPTIONS and SORT_OPTIONS[sort]:
            query_params.append(SORT_OPTIONS[sort])

        if query_params:
            url = f"{url}?{'&'.join(query_params)}"

        soup = fetch_soup(url)
        return parse_search_results(soup)

    def get_info(self, restaurant_id: str, url: str | None = None) -> RestaurantDetail | None:
        """Get detailed info for a restaurant by ID or URL.

        Args:
            restaurant_id: Restaurant ID
            url: Optional URL (skips URL guessing if provided)
        """
        # If URL provided, use it directly
        if url:
            soup = fetch_soup(url)
            return parse_restaurant_detail(soup, restaurant_id, url)

        # Region prefixes: ID prefix -> (region_name, area_prefix)
        region_map = {
            "13": ("tokyo", "13"),    # Tokyo
            "27": ("osaka", "27"),    # Osaka
            "26": ("kyoto", "26"),    # Kyoto
            "40": ("fukuoka", "40"),  # Fukuoka
            "01": ("hokkaido", "01"), # Hokkaido
            "23": ("aichi", "23"),    # Aichi/Nagoya
            "14": ("kanagawa", "14"), # Kanagawa/Yokohama
        }

        # Try to determine region from ID prefix
        prefix = restaurant_id[:2]
        if prefix in region_map:
            region, area_prefix = region_map[prefix]
            # Build all possible URLs and try in parallel
            urls = []
            for sub in ["01", "02", "03", "04", "05"]:
                area_code = f"A{area_prefix}01/A{area_prefix}01{sub}"
                urls.append(f"{BASE_URL}/{region}/{area_code}/{restaurant_id}/")

            # Fetch all in parallel
            try:
                soups = fetch_soups_parallel(urls)
                for soup, url in zip(soups, urls):
                    try:
                        result = parse_restaurant_detail(soup, restaurant_id, url)
                        if result:
                            return result
                    except Exception:
                        continue
            except Exception:
                pass

        # Fallback: search and verify ID matches
        results = self.search(query=restaurant_id)
        if results and results[0].id == restaurant_id:
            url = results[0].url
            soup = fetch_soup(url)
            return parse_restaurant_detail(soup, restaurant_id, url)
        return None

    def get_reviews(
        self,
        restaurant_id: str | None = None,
        url: str | None = None,
        page: int = 1,
        max_pages: int = 1,
    ) -> tuple[str, str, list[Review]]:
        """Fetch reviews for a restaurant. Returns (name, rating, reviews).

        Args:
            restaurant_id: Restaurant ID
            url: Restaurant URL
            page: Starting page (1-indexed)
            max_pages: Maximum number of pages to fetch (default 1)

        Uses parallel fetching when max_pages > 1 for better performance.
        """
        # Build base review URL
        if url:
            if "/dtlrvwlst/" not in url:
                base_url = url.rstrip("/") + "/dtlrvwlst/"
            else:
                base_url = url.split("/dtlrvwlst/")[0] + "/dtlrvwlst/"
        elif restaurant_id:
            info = self.get_info(restaurant_id)
            if info:
                base_url = info.url.rstrip("/") + "/dtlrvwlst/"
            else:
                raise ValueError(f"Restaurant {restaurant_id} not found")
        else:
            raise ValueError("Must provide either restaurant_id or url")

        # Build list of URLs to fetch
        urls = []
        for pg in range(page, page + max_pages):
            if pg == 1:
                urls.append(base_url)
            else:
                urls.append(f"{base_url}COND-0/smp1/?smp=1&lc=0&rvw_part=all&PG={pg}")

        # Fetch all pages in parallel
        soups = fetch_soups_parallel(urls)

        # Parse results
        all_reviews: list[Review] = []
        restaurant_name = ""
        overall_rating = ""

        for soup in soups:
            name, rating, reviews = parse_reviews(soup)

            if not restaurant_name:
                restaurant_name = name
                overall_rating = rating

            if not reviews:
                break  # No more reviews

            all_reviews.extend(reviews)

        return restaurant_name, overall_rating, all_reviews

    def get_areas(self, region: str) -> list[Area]:
        """Fetch areas for a region dynamically."""
        url = f"{BASE_URL}/{region}/"
        soup = fetch_soup(url)
        return parse_areas(soup)

    def list_genres(self) -> list[tuple[str, str, str]]:
        """List all available genres. Returns [(slug, japanese, english), ...]."""
        return list_genres()

    def get_info_batch(
        self,
        restaurant_ids: list[str],
        urls: list[str] | None = None,
    ) -> list[RestaurantDetail | None]:
        """Get detailed info for multiple restaurants in parallel.

        Args:
            restaurant_ids: List of restaurant IDs
            urls: Optional list of URLs (same order as IDs) - skips URL guessing

        Returns:
            List of RestaurantDetail (or None if not found), in same order as input
        """
        if not restaurant_ids:
            return []
        if len(restaurant_ids) == 1:
            url = urls[0] if urls else None
            return [self.get_info(restaurant_ids[0], url=url)]

        # If URLs provided, use them directly
        if urls and len(urls) == len(restaurant_ids):
            soups = fetch_soups_parallel(urls)
            results = []
            for rid, soup, url in zip(restaurant_ids, soups, urls):
                try:
                    detail = parse_restaurant_detail(soup, rid, url)
                    results.append(detail)
                except Exception:
                    results.append(None)
            return results

        # Build URLs for each restaurant - try common area patterns
        region_map = {
            "13": "tokyo",
            "27": "osaka",
            "26": "kyoto",
            "40": "fukuoka",
            "01": "hokkaido",
            "23": "aichi",
            "14": "kanagawa",
        }

        built_urls = []
        for rid in restaurant_ids:
            prefix = rid[:2]
            if prefix in region_map:
                region = region_map[prefix]
                area_code = f"A{prefix}01/A{prefix}0101"
                built_urls.append(f"{BASE_URL}/{region}/{area_code}/{rid}/")
            else:
                built_urls.append("")  # Will need fallback

        # Fetch all valid URLs in parallel
        valid_indices = [i for i, u in enumerate(built_urls) if u]
        valid_urls = [built_urls[i] for i in valid_indices]

        if not valid_urls:
            return [self.get_info(rid) for rid in restaurant_ids]

        soups = fetch_soups_parallel(valid_urls)

        # Parse results
        results: list[RestaurantDetail | None] = [None] * len(restaurant_ids)
        for idx, soup, url in zip(valid_indices, soups, valid_urls):
            rid = restaurant_ids[idx]
            try:
                detail = parse_restaurant_detail(soup, rid, url)
                if detail:
                    results[idx] = detail
                else:
                    results[idx] = self.get_info(rid)
            except Exception:
                results[idx] = self.get_info(rid)

        # Handle any that didn't have valid URLs
        for i, rid in enumerate(restaurant_ids):
            if results[i] is None and not built_urls[i]:
                results[i] = self.get_info(rid)

        return results

    def get_reviews_batch(
        self,
        restaurant_ids: list[str],
        urls: list[str] | None = None,
        max_pages: int = 1,
    ) -> list[tuple[str, str, list[Review]]]:
        """Fetch reviews for multiple restaurants in parallel.

        Args:
            restaurant_ids: List of restaurant IDs
            urls: Optional list of restaurant URLs (skips info lookup)
            max_pages: Pages per restaurant (default 1)

        Returns:
            List of (name, rating, reviews) tuples, in same order as input
        """
        if not restaurant_ids:
            return []

        # If URLs provided, use them directly; otherwise fetch info
        if urls and len(urls) == len(restaurant_ids):
            base_urls = [u.rstrip("/") + "/dtlrvwlst/" for u in urls]
        else:
            infos = self.get_info_batch(restaurant_ids, urls=urls)
            base_urls = [
                info.url.rstrip("/") + "/dtlrvwlst/" if info else ""
                for info in infos
            ]

        # Build review URLs for each restaurant
        all_urls = []
        url_to_restaurant: list[int] = []  # Track which restaurant each URL belongs to

        for i, base_url in enumerate(base_urls):
            if base_url:
                for pg in range(1, max_pages + 1):
                    if pg == 1:
                        all_urls.append(base_url)
                    else:
                        all_urls.append(f"{base_url}COND-0/smp1/?smp=1&lc=0&rvw_part=all&PG={pg}")
                    url_to_restaurant.append(i)

        # Fetch all review pages in parallel
        soups = fetch_soups_parallel(all_urls)

        # Parse and group by restaurant
        results: list[tuple[str, str, list[Review]]] = [("", "", []) for _ in restaurant_ids]
        restaurant_reviews: dict[int, list[Review]] = {i: [] for i in range(len(restaurant_ids))}
        restaurant_meta: dict[int, tuple[str, str]] = {}

        for soup, restaurant_idx in zip(soups, url_to_restaurant):
            try:
                name, rating, reviews = parse_reviews(soup)
                if restaurant_idx not in restaurant_meta:
                    restaurant_meta[restaurant_idx] = (name, rating)
                restaurant_reviews[restaurant_idx].extend(reviews)
            except Exception:
                continue

        # Build final results
        for i in range(len(restaurant_ids)):
            name, rating = restaurant_meta.get(i, ("", ""))
            results[i] = (name, rating, restaurant_reviews[i])

        return results
