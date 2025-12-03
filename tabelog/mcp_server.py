"""FastMCP server for Tabelog Explorer.

Tabelog (食べログ) is Japan's largest restaurant review site with millions of
user reviews. Ratings are notoriously strict - a 3.5+ is considered excellent,
and 4.0+ is exceptional. Most good restaurants score between 3.0-3.8.
"""

from dataclasses import asdict

from fastmcp import FastMCP

from tabelog.client import FILTERS, TabelogClient

# Create FastMCP server instance
mcp = FastMCP("Tabelog Explorer")

# Shared client instance
_client = TabelogClient()


@mcp.tool
def search_restaurants(
    query: str | None = None,
    area: str | None = None,
    genre: str | None = None,
    filters: list[str] | None = None,
    sort: str = "trend",
    limit: int = 20,
) -> list[dict]:
    """Search Tabelog, Japan's largest restaurant review site.

    Tabelog ratings are strict: 3.5+ is excellent, 4.0+ is exceptional.
    Most quality restaurants score 3.0-3.8.

    Args:
        query: Free-text search (e.g., "焼肉", "omakase", restaurant name)
        area: Region or specific area. Common regions:
              - "tokyo", "osaka", "kyoto", "fukuoka", "hokkaido", "nagoya"
              - For specific areas: "tokyo/A1301" (Ginza), "tokyo/A1303" (Shibuya)
              - Use get_areas("tokyo") to discover area codes
        genre: Cuisine type slug. Popular options:
              - Japanese: "sushi", "ramen", "izakaya", "yakitori", "tempura", "udon", "soba"
              - Meat: "yakiniku" (BBQ), "sukiyaki", "shabu", "tonkatsu", "kushikatsu"
              - Other: "curry", "italian", "french", "chinese", "cafe"
              - Use list_genres() for complete list
        filters: Venue requirements (combine multiple):
              - "private_room", "non_smoking", "lunch", "reservable"
              - "solo" (solo-friendly), "date", "kids_ok"
              - "counter", "tatami", "parking", "sunday_open"
              - "all_you_can_drink", "all_you_can_eat", "card_ok"
        sort: "trend" (default/popular), "rating" (highest rated), "reviews" (most reviewed)
        limit: Max results (default 20)

    Returns:
        List of restaurants, each with:
        - id: Use with get_restaurant_info() or get_reviews()
        - name, rating (e.g., "3.58"), area, cuisine, url
        - price_lunch, price_dinner (e.g., "¥1,000~¥1,999")
        - review_count, save_count (popularity indicators)
        - description: Promotional tagline
        - review_snippet: Featured review with title, text, reviewer

    Example workflow:
        1. search_restaurants(area="tokyo", genre="sushi", sort="rating")
        2. get_restaurant_info(id) for details on interesting finds
        3. get_reviews(id, max_pages=2) for in-depth feedback
    """
    results = _client.search(
        query=query,
        area=area,
        genre=genre,
        filters=filters,
        sort=sort,
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
    """Get comprehensive details for a specific restaurant.

    Use this after search_restaurants() to get full info on restaurants of interest.
    Provides everything needed to recommend or book a restaurant.

    Args:
        restaurant_id: Restaurant ID from search results (e.g., "13002251")

    Returns:
        Full details including:
        - Basic: id, name, rating, cuisine, url
        - Location: address, access (nearest station/directions)
        - Prices: price_lunch, price_dinner (e.g., "¥3,000~¥3,999")
        - Hours: hours (opening times, holidays)
        - Contact: phone, reservable (online booking available)
        - Reservation: reservation_status (e.g., "予約可")
        - Courses: List of set menus with name, price, num_items
        - Facilities: seats, private_room, smoking, parking
        - Payment: payment_methods, service_charge

        Returns None if restaurant not found.

    Note: The ID is region-specific (13=Tokyo, 27=Osaka, 26=Kyoto, etc.)
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
    """Fetch detailed user reviews for a restaurant.

    Reviews are in Japanese. Each page has ~20 reviews.
    Use max_pages > 1 to get more reviews (fetched in parallel for speed).

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

    Tips:
        - Start with max_pages=1 to sample reviews
        - Use max_pages=3-5 for thorough analysis
        - Reviews are sorted by recency (newest first)
        - Look for specific dish mentions, service comments, ambiance notes
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
def get_restaurant_info_batch(restaurant_ids: list[str]) -> list[dict | None]:
    """Get comprehensive details for multiple restaurants in parallel.

    Much faster than calling get_restaurant_info() multiple times.
    Use after search_restaurants() to enrich top results with full details.

    Args:
        restaurant_ids: List of restaurant IDs from search results

    Returns:
        List of restaurant details (same order as input).
        Each contains: name, rating, address, phone, hours, courses,
        reservable, private_room, etc. None if restaurant not found.

    Example:
        results = search_restaurants(area="tokyo", genre="sushi", limit=5)
        ids = [r["id"] for r in results]
        details = get_restaurant_info_batch(ids)  # Fetches all 5 in parallel
    """
    details = _client.get_info_batch(restaurant_ids)
    return [asdict(d) if d else None for d in details]


@mcp.tool
def get_reviews_batch(
    restaurant_ids: list[str],
    max_pages: int = 1,
) -> list[dict]:
    """Fetch reviews for multiple restaurants in parallel.

    Much faster than calling get_reviews() multiple times.
    Useful for comparing reviews across restaurants or analyzing trends.

    Args:
        restaurant_ids: List of restaurant IDs
        max_pages: Review pages per restaurant (default 1, ~20 reviews each)

    Returns:
        List of review data (same order as input), each with:
        - restaurant_name, rating
        - reviews: List of {rating, title, body, visit_date}

    Example:
        results = search_restaurants(area="tokyo", genre="ramen", sort="rating", limit=3)
        ids = [r["id"] for r in results]
        all_reviews = get_reviews_batch(ids, max_pages=2)  # ~40 reviews per restaurant
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
