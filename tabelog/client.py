"""Tabelog API client."""

from urllib.parse import quote

from ._http import BASE_URL, fetch_soup, fetch_soups_parallel
from ._parse import parse_areas, parse_restaurant_detail, parse_reviews, parse_search_results
from .genres import GENRES, get_genre_url, list_genres
from .models import Area, Restaurant, RestaurantDetail, Review

# Price tier mappings: value -> yen amount
# Value 0 means "no limit", values 1-16 map to specific yen amounts
# Note: The progression is not linear (e.g., 7 = ¥8,000, not ¥7,000)
PRICE_TIERS = {
    0: None,      # No limit
    1: 1000,
    2: 2000,
    3: 3000,
    4: 4000,
    5: 5000,
    6: 6000,
    7: 8000,      # Note: jumps from 6k to 8k
    8: 10000,
    9: 15000,
    10: 20000,
    11: 30000,
    12: 40000,
    13: 50000,
    14: 60000,
    15: 80000,
    16: 100000,
}

# Reverse mapping: yen amount -> tier value
YEN_TO_TIER = {v: k for k, v in PRICE_TIERS.items() if v is not None}


def get_price_tier(yen: int | None) -> int:
    """Convert yen amount to Tabelog price tier value.

    Args:
        yen: Price in yen (e.g., 3000 for ¥3,000). None means no limit.

    Returns:
        Tier value 0-16 for use in URL parameters.
        Returns closest tier that doesn't exceed the requested amount for max,
        or closest tier that meets/exceeds the amount for min.
    """
    if yen is None:
        return 0

    # Find exact match first
    if yen in YEN_TO_TIER:
        return YEN_TO_TIER[yen]

    # Find closest tier
    sorted_amounts = sorted(YEN_TO_TIER.keys())
    for amount in sorted_amounts:
        if amount >= yen:
            return YEN_TO_TIER[amount]

    # If yen is higher than max tier, return max
    return 16


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
        keyword: str | None = None,
        area: str | None = None,
        genre: str | None = None,
        filters: list[str] | None = None,
        sort: str | None = None,
        open_at: str | None = None,
        price_min: int | None = None,
        price_max: int | None = None,
        meal_type: str | None = None,
    ) -> list[Restaurant]:
        """Search for restaurants.

        Args:
            keyword: Location or restaurant name to search (e.g., '成田空港', '銀座', 'Sukiyabashi Jiro').
                     Do NOT include cuisine types here - use 'genre' parameter instead.
            area: Area code (e.g., 'tokyo', 'tokyo/A1301')
            genre: Genre slug (e.g., 'ramen', 'sushi', 'yoshoku')
            filters: List of filter names (e.g., ['private_room', 'non_smoking'])
            sort: Sort order ('trend', 'rating', 'reviews')
            open_at: Filter by open time in HH:MM format (e.g., '19:00', '12:30')
                     Use 'now' to filter by current time (Japan timezone)
            price_min: Minimum budget in yen (e.g., 1000 for ¥1,000). Server rounds to nearest tier.
            price_max: Maximum budget in yen (e.g., 5000 for ¥5,000). Server rounds to nearest tier.
            meal_type: 'lunch' or 'dinner' - required when using price filters.
                       Determines which budget (lunch/dinner) to filter on.
                       Note: Lunch filtering works well. Dinner filtering is best effort as
                       Tabelog's URL-based dinner price filtering has limitations.
        """
        # Validate price filter usage
        if (price_min is not None or price_max is not None) and meal_type not in ("lunch", "dinner"):
            raise ValueError("meal_type must be 'lunch' or 'dinner' when using price filters")

        # Build base URL
        if area:
            base = f"{BASE_URL}/{area}"
        else:
            base = BASE_URL

        # Build path: rstLst/[lunch]/[filter]/[genre]/
        # Note: Only ONE filter can be in the path. Additional filters go in query params.
        # IMPORTANT: Lunch uses /lunch/ in path, but dinner does NOT use /dinner/ in path.
        # Dinner price filters are applied via query params only (DnrCos, DnrCosT).
        url = f"{base}/rstLst/"

        # Add lunch to path if specified (dinner does NOT go in path)
        if meal_type == "lunch":
            url = url.rstrip("/") + "/lunch/"

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
        if keyword:
            query_params.insert(0, f"vs=1&sw={quote(keyword)}")

        # Add sort params
        if sort and sort in SORT_OPTIONS and SORT_OPTIONS[sort]:
            query_params.append(SORT_OPTIONS[sort])

        # Add open_at time filter
        if open_at:
            if open_at.lower() == "now":
                # Get current time in Japan timezone (UTC+9)
                from datetime import datetime, timezone, timedelta
                jst = timezone(timedelta(hours=9))
                now = datetime.now(jst)
                hh, mm = now.hour, now.minute
            else:
                # Parse HH:MM format
                parts = open_at.split(":")
                hh = int(parts[0])
                mm = int(parts[1]) if len(parts) > 1 else 0
            query_params.append(f"hh={hh}&hm={mm:02d}")

        # Add price filter params
        # Lunch uses: LstCos (min), LstCosT (max)
        # Dinner uses: DnrCos (min), DnrCosT (max)
        # RdoCosTp=1 enables price filtering
        if price_min is not None or price_max is not None:
            query_params.append("RdoCosTp=1")
            min_tier = get_price_tier(price_min)
            max_tier = get_price_tier(price_max)

            if meal_type == "lunch":
                query_params.append(f"LstCos={min_tier}")
                query_params.append(f"LstCosT={max_tier}")
            else:  # dinner
                query_params.append(f"DnrCos={min_tier}")
                query_params.append(f"DnrCosT={max_tier}")

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
            "01": ("hokkaido", "01"),   # Hokkaido
            "11": ("saitama", "11"),    # Saitama
            "12": ("chiba", "12"),      # Chiba
            "13": ("tokyo", "13"),      # Tokyo
            "14": ("kanagawa", "14"),   # Kanagawa/Yokohama
            "22": ("shizuoka", "22"),   # Shizuoka
            "23": ("aichi", "23"),      # Aichi/Nagoya
            "26": ("kyoto", "26"),      # Kyoto
            "27": ("osaka", "27"),      # Osaka
            "28": ("hyogo", "28"),      # Hyogo/Kobe
            "34": ("hiroshima", "34"),  # Hiroshima
            "40": ("fukuoka", "40"),    # Fukuoka
            "47": ("okinawa", "47"),    # Okinawa
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
            "01": "hokkaido",
            "11": "saitama",
            "12": "chiba",
            "13": "tokyo",
            "14": "kanagawa",
            "22": "shizuoka",
            "23": "aichi",
            "26": "kyoto",
            "27": "osaka",
            "28": "hyogo",
            "34": "hiroshima",
            "40": "fukuoka",
            "47": "okinawa",
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
