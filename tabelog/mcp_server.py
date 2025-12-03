"""FastMCP server for Tabelog Explorer.

Tabelog (食べログ) is Japan's largest restaurant review site with millions of
user reviews. Ratings are notoriously strict - a 3.5+ is considered excellent,
and 4.0+ is exceptional. Most good restaurants score between 3.0-3.8.
"""

import json
from dataclasses import asdict

from fastmcp import FastMCP

from tabelog.client import FILTERS, PRICE_TIERS, TabelogClient


def _parse_filters(filters: str | list[str] | None) -> list[str] | None:
    """Parse filters from various input formats.

    Handles:
    - None -> None
    - [] -> None
    - ["solo", "counter"] -> ["solo", "counter"]
    - '["solo", "counter"]' (JSON string) -> ["solo", "counter"]
    - "solo,counter" (comma-separated) -> ["solo", "counter"]
    - "solo" (single value) -> ["solo"]
    """
    if filters is None:
        return None

    if isinstance(filters, list):
        return filters if filters else None

    # String input - try JSON first, then comma-separated
    filters = filters.strip()
    if not filters:
        return None

    if filters.startswith("["):
        try:
            parsed = json.loads(filters)
            return parsed if parsed else None
        except json.JSONDecodeError:
            pass

    # Comma-separated or single value
    result = [f.strip() for f in filters.split(",") if f.strip()]
    return result if result else None

# Create FastMCP server instance
mcp = FastMCP("Tabelog Explorer")

# Shared client instance
_client = TabelogClient()


@mcp.tool
def search_restaurants(
    keyword: str | None = None,
    area: str | None = None,
    genre: str | None = None,
    filters: str | None = None,
    sort: str = "trend",
    open_at: str | None = None,
    price_min: int | None = None,
    price_max: int | None = None,
    meal_type: str | None = None,
    limit: int = 20,
) -> list[dict]:
    """Search Tabelog, Japan's largest restaurant review site.

    Tabelog ratings are strict: 3.5+ is excellent, 4.0+ is exceptional.
    Most quality restaurants score 3.0-3.8.

    Args:
        keyword: Location or restaurant name to search (e.g., "成田空港", "銀座", "Sukiyabashi Jiro").
                 ⚠️ Do NOT put cuisine types here - use 'genre' parameter instead.
        area: Region or specific area. Common regions:
              - "tokyo", "osaka", "kyoto", "fukuoka", "hokkaido", "nagoya"
              - "chiba" (Narita Airport), "kanagawa" (Yokohama)
              - For specific areas: "tokyo/A1301" (Ginza), "tokyo/A1303" (Shibuya)
              - Use get_areas("tokyo") to discover area codes
        genre: Cuisine type slug. Popular options:
              - Japanese: "sushi", "ramen", "izakaya", "yakitori", "tempura", "udon", "soba"
              - Meat: "yakiniku" (BBQ), "tonkatsu"
              - Western: "yoshoku" (洋食), "italian", "french", "curry"
              - Other: "chinese", "cafe"
              - Use list_genres() for complete list
        filters: Venue requirements - comma-separated string (e.g., "solo,counter,card_ok").
                 Available: "private_room", "non_smoking", "lunch", "reservable",
                 "solo", "date", "kids_ok", "counter", "tatami", "parking",
                 "sunday_open", "all_you_can_drink", "all_you_can_eat", "card_ok"
        sort: "trend" (default/popular), "rating" (highest rated), "reviews" (most reviewed)
        open_at: Filter by open time. Use "now" for current Japan time,
                 or specify time like "19:00", "12:30"
        price_min: Minimum budget in yen (e.g., 1000 for ¥1,000).
                   Rounds to nearest tier: 1000, 2000, 3000, 4000, 5000, 6000, 8000,
                   10000, 15000, 20000, 30000, 40000, 50000, 60000, 80000, 100000.
                   Use list_price_tiers() to see all options.
        price_max: Maximum budget in yen (e.g., 5000 for ¥5,000). Same tier rounding.
        meal_type: "lunch" or "dinner" - REQUIRED when using price filters.
                   Determines which meal budget to filter on.
        limit: Max results (default 20)

    Returns:
        List of restaurants, each with:
        - id: Restaurant ID - use this with batch methods
        - url, name, rating (e.g., "3.58"), area, cuisine
        - price_lunch, price_dinner (e.g., "¥1,000~¥1,999")
        - review_count, save_count (popularity indicators)
        - description: Promotional tagline
        - review_snippet: Featured review with title, text, reviewer

    Examples:
        # Budget lunch under ¥2,000 in Tokyo
        search_restaurants(area="tokyo", meal_type="lunch", price_max=2000)

        # Mid-range dinner ¥5,000-¥10,000 sushi in Ginza
        search_restaurants(area="tokyo/A1301", genre="sushi", meal_type="dinner",
                          price_min=5000, price_max=10000)

        # High-end dinner ¥20,000+ omakase
        search_restaurants(genre="sushi", meal_type="dinner", price_min=20000)

    IMPORTANT - After searching, use BATCH methods for multiple restaurants:
        results = search_restaurants(area="tokyo", genre="sushi", limit=5)
        ids = [r["id"] for r in results]

        # Use batch methods - NOT individual calls in a loop:
        details = get_restaurant_info_batch(ids)  # Parallel fetch
        reviews = get_reviews_batch(ids)          # Parallel fetch
    """
    parsed_filters = _parse_filters(filters)
    results = _client.search(
        keyword=keyword,
        area=area,
        genre=genre,
        filters=parsed_filters,
        sort=sort,
        open_at=open_at,
        price_min=price_min,
        price_max=price_max,
        meal_type=meal_type,
    )
    return [asdict(r) for r in results[:limit]]


@mcp.tool
def get_areas(region: str) -> list[dict]:
    """Get neighborhood/district codes for filtering searches by specific area.

    Use this to narrow searches to specific neighborhoods (e.g., Ginza, Shibuya, Shinjuku).
    Pass the returned 'code' to search_restaurants(area="tokyo/CODE").

    Args:
        region: Main region - "tokyo", "osaka", "kyoto", "fukuoka", "hokkaido",
                "aichi" (Nagoya), "kanagawa" (Yokohama)

    Returns:
        List of areas with:
        - code: Area code to use in search (e.g., "A1301" for Ginza)
        - name: Japanese area name (e.g., "銀座・新橋・有楽町")
        - parent_code: Parent area if this is a sub-area

    Example:
        areas = get_areas("tokyo")
        # Returns areas like: {"code": "A1301", "name": "銀座・新橋・有楽町", ...}
        # Then search: search_restaurants(area="tokyo/A1301", genre="sushi")
    """
    areas = _client.get_areas(region)
    return [asdict(a) for a in areas]


@mcp.tool
def list_genres() -> list[dict]:
    """List all cuisine/restaurant type slugs for filtering searches.

    Returns slugs to use with search_restaurants(genre="slug").

    Common genres (no need to call this for these):
    - Staples: "ramen", "sushi", "izakaya", "yakitori", "udon", "soba", "tempura"
    - Meat: "yakiniku", "sukiyaki", "shabu", "tonkatsu", "kushikatsu", "steak"
    - Other Japanese: "kaiseki", "oden", "okonomiyaki", "takoyaki", "donburi"
    - International: "italian", "french", "chinese", "korean", "thai", "curry"
    - Casual: "cafe", "bar", "bakery", "sweets"

    Call this tool only if you need the complete list or less common genres.

    Returns:
        List with slug (use in search), japanese name, english name
    """
    genres = _client.list_genres()
    return [{"slug": slug, "japanese": ja, "english": en} for slug, ja, en in genres]


@mcp.tool
def get_restaurant_info(restaurant_id: str) -> dict | None:
    """Get comprehensive details for a single restaurant.

    ⚠️  FOR MULTIPLE RESTAURANTS: Use get_restaurant_info_batch() instead!
        It's much faster (parallel fetching) and you already have URLs from search.

    Args:
        restaurant_id: Restaurant ID from search results (e.g., "13002251")

    Returns:
        Full details including:
        - Basic: id, name, rating, cuisine, url
        - Location: address, access (nearest station/walking time, e.g., "新橋駅から徒歩3分")
        - Prices: price_lunch, price_dinner (e.g., "¥3,000~¥3,999")
        - Hours: hours (full text), last_order (e.g., "21:30" or "料理23:00 ドリンク23:30"),
                 closed_days (e.g., "日・祝日" or "無休" for no holidays)
        - Contact: phone, reservable (online booking available)
        - Reservation: reservation_status (e.g., "予約可", may include cancellation policy)
        - Courses: List of set menus with name, price, num_items
        - Facilities: seats, private_room, smoking, parking
        - Payment: payment_methods, service_charge

        Returns None if restaurant not found.
    """
    details = _client.get_info(restaurant_id)
    if details:
        return asdict(details)
    return None


@mcp.tool
def get_reviews(
    restaurant_id: str | None = None,
    url: str | None = None,
    page: int = 1,
    max_pages: int = 1,
) -> dict:
    """Fetch detailed user reviews for a single restaurant.

    ⚠️  FOR MULTIPLE RESTAURANTS: Use get_reviews_batch() instead!
        It's much faster (parallel fetching) and you already have URLs from search.

    Reviews are in Japanese. Each page has ~20 reviews.

    Args:
        restaurant_id: Restaurant ID from search results (preferred)
        url: Full Tabelog URL (alternative, use if you have the URL)
        page: Starting page (default: 1, most recent reviews first)
        max_pages: Pages to fetch (default: 1, ~20 reviews per page)

    Returns:
        - restaurant_name: Restaurant name
        - rating: Overall rating (e.g., "3.64")
        - reviews: List of reviews, each with:
          - rating: Individual review score (e.g., "4.0")
          - title: Review headline (may be empty)
          - body: Full review text (Japanese)
          - visit_date: When reviewer visited
    """
    if not restaurant_id and not url:
        return {"error": "Must provide either restaurant_id or url"}

    try:
        name, rating, reviews = _client.get_reviews(
            restaurant_id=restaurant_id,
            url=url,
            page=page,
            max_pages=max_pages,
        )
        return {
            "restaurant_name": name,
            "rating": rating,
            "reviews": [asdict(r) for r in reviews],
        }
    except ValueError as e:
        return {"error": str(e)}


@mcp.tool
def get_restaurant_info_batch(
    restaurant_ids: list[str],
) -> list[dict | None]:
    """Get comprehensive details for multiple restaurants in parallel.

    🚀 ALWAYS USE THIS instead of calling get_restaurant_info() in a loop!
       5 restaurants: ~1.5s (batch) vs ~7s (sequential)

    Args:
        restaurant_ids: List of restaurant IDs from search results.
                        ONLY pass IDs, not URLs.

    Returns:
        List of restaurant details (same order as input).
        Each contains: name, rating, address, access (station/walking time),
        phone, hours, last_order, closed_days, courses, reservable,
        reservation_status, private_room, etc. None if restaurant not found.

    Example:
        results = search_restaurants(area="tokyo", genre="sushi", limit=5)
        ids = [r["id"] for r in results]
        details = get_restaurant_info_batch(ids)
    """
    details = _client.get_info_batch(restaurant_ids)
    return [asdict(d) if d else None for d in details]


@mcp.tool
def get_reviews_batch(
    restaurant_ids: list[str],
    max_pages: int = 1,
) -> list[dict]:
    """Fetch reviews for multiple restaurants in parallel.

    🚀 ALWAYS USE THIS instead of calling get_reviews() in a loop!
       3 restaurants × 2 pages: ~2s (batch) vs ~12s (sequential)

    Args:
        restaurant_ids: List of restaurant IDs. ONLY pass IDs, not URLs.
        max_pages: Review pages per restaurant (default 1, ~20 reviews each)

    Returns:
        List of review data (same order as input), each with:
        - restaurant_name, rating
        - reviews: List of {rating, title, body, visit_date}

    Example:
        results = search_restaurants(area="tokyo", genre="ramen", limit=3)
        ids = [r["id"] for r in results]
        all_reviews = get_reviews_batch(ids, max_pages=2)
    """
    results = _client.get_reviews_batch(restaurant_ids, max_pages=max_pages)
    return [
        {
            "restaurant_name": name,
            "rating": rating,
            "reviews": [asdict(r) for r in reviews],
        }
        for name, rating, reviews in results
    ]


@mcp.tool
def list_available_filters() -> list[dict]:
    """List all search filters for search_restaurants().

    Common filters (no need to call this for these):
    - "private_room": Has private rooms (個室) - for groups/business
    - "non_smoking": Non-smoking venue (禁煙)
    - "lunch": Serves lunch (ランチ) - important as many dinner-only
    - "reservable": Online reservation available (ネット予約可)
    - "solo": Solo-dining friendly (一人で入りやすい) - for counter seats
    - "date": Romantic/date-appropriate (デート向け)

    Call this only if you need the complete list.

    Returns:
        List of filters with 'name' (use in search) and 'description'
    """
    filter_descriptions = {
        "private_room": "Has private room (個室) - for groups, business dinners",
        "non_smoking": "Non-smoking (禁煙) - entire venue",
        "lunch": "Lunch available (ランチ) - many places are dinner-only",
        "reservable": "Online reservation (ネット予約可)",
        "all_you_can_drink": "All-you-can-drink (飲み放題) - nomihoudai",
        "all_you_can_eat": "All-you-can-eat (食べ放題) - tabehoudai",
        "card_ok": "Credit cards accepted (カード可) - many Japan spots are cash-only",
        "parking": "Has parking (駐車場)",
        "kids_ok": "Children welcome (子供可)",
        "sunday_open": "Open Sundays (日曜営業) - many restaurants closed",
        "solo": "Solo-friendly (一人で入りやすい) - counter seating, welcoming",
        "date": "Good for dates (デート向け) - romantic ambiance",
        "counter": "Has counter seats (カウンター席) - watch the chef",
        "tatami": "Has tatami seating (座敷) - traditional floor seating",
    }
    return [
        {"name": name, "description": desc}
        for name, desc in filter_descriptions.items()
    ]


@mcp.tool
def list_price_tiers() -> list[dict]:
    """List all price tier options for budget filtering.

    Tabelog uses fixed price tiers (not arbitrary yen amounts). When you pass
    price_min or price_max to search_restaurants(), the value is rounded to
    the nearest tier.

    Common price ranges:
    - Budget lunch: price_max=1000 or 2000 (under ¥1,000 or ¥2,000)
    - Mid-range: price_min=3000, price_max=5000 (¥3,000-¥5,000)
    - High-end dinner: price_min=10000, price_max=20000 (¥10,000-¥20,000)
    - Premium omakase: price_min=30000 (¥30,000+)

    Call this only if you need the exact tier boundaries.

    Returns:
        List of price tiers with 'yen' amount and 'display' string
    """
    return [
        {"yen": yen, "display": f"¥{yen:,}"}
        for yen in sorted(PRICE_TIERS.values())
        if yen is not None
    ]
