"""FastMCP server for Tabelog Explorer."""

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
    """Search for restaurants on Tabelog.

    Args:
        query: Search keyword (e.g., "sushi", "ramen")
        area: Area code (e.g., "tokyo", "osaka", "tokyo/A1301")
        genre: Cuisine type slug (e.g., "ramen", "sushi", "izakaya").
               Use list_genres tool to see all available options.
        filters: List of filter names. Use list_available_filters to see options.
        sort: Sort order - "trend" (default), "rating" (highest first), "reviews" (most reviews)
        limit: Maximum number of results (default: 20)

    Returns:
        List of restaurant dictionaries with:
        - id, name, rating, area, cuisine, url
        - description, review_count, save_count
        - price_lunch, price_dinner
        - review_snippet (title, text, reviewer) - a featured review preview
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
    """Get available areas for a region.

    Args:
        region: Region name (e.g., "tokyo", "osaka", "kyoto", "fukuoka", "hokkaido")

    Returns:
        List of area dictionaries with code, name, and parent_code
    """
    areas = _client.get_areas(region)
    return [asdict(a) for a in areas]


@mcp.tool
def list_genres() -> list[dict]:
    """List all available cuisine types (genres).

    Returns:
        List of genre dictionaries with slug, japanese name, and english name
    """
    genres = _client.list_genres()
    return [{"slug": slug, "japanese": ja, "english": en} for slug, ja, en in genres]


@mcp.tool
def get_restaurant_info(restaurant_id: str) -> dict | None:
    """Get detailed information for a restaurant.

    Args:
        restaurant_id: The Tabelog restaurant ID (e.g., "13002251")

    Returns:
        Restaurant detail dictionary with name, rating, address, cuisine,
        price_lunch, price_dinner, hours, url. Returns None if not found.
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
    """Fetch reviews for a restaurant.

    Args:
        restaurant_id: The Tabelog restaurant ID (e.g., "13002251")
        url: Restaurant URL (alternative to restaurant_id)
        page: Starting page number (default: 1)
        max_pages: Number of pages to fetch (default: 1)

    Returns:
        Dictionary with restaurant_name, rating, and list of review dictionaries
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
def list_available_filters() -> list[dict]:
    """List all available search filters.

    Returns:
        List of filter dictionaries with name and description
    """
    filter_descriptions = {
        "private_room": "Has private room (個室)",
        "non_smoking": "Non-smoking (禁煙)",
        "lunch": "Lunch available (ランチ)",
        "reservable": "Online reservation (ネット予約可)",
        "all_you_can_drink": "All-you-can-drink (飲み放題)",
        "all_you_can_eat": "All-you-can-eat (食べ放題)",
        "card_ok": "Card accepted (カード可)",
        "parking": "Has parking (駐車場)",
        "kids_ok": "Kids welcome (子供可)",
        "sunday_open": "Open on Sunday (日曜営業)",
        "solo": "Solo-friendly (一人で入りやすい)",
        "date": "Good for dates (デート向け)",
        "counter": "Has counter seats (カウンター席)",
        "tatami": "Has tatami seating (座敷)",
    }
    return [
        {"name": name, "description": desc}
        for name, desc in filter_descriptions.items()
    ]
