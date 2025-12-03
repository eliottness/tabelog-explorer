"""CLI interface for Tabelog Explorer."""

import click

from . import __version__
from .client import TabelogClient

client = TabelogClient()


@click.group()
@click.version_option(version=__version__)
def main():
    """Tabelog Explorer - Browse and search Japanese restaurant reviews."""
    pass


@main.command()
@click.argument("query", required=False)
@click.option("--area", "-a", help="Filter by area (e.g., tokyo, tokyo/A1301)")
@click.option("--genre", "-g", help="Filter by cuisine type (e.g., ramen, sushi)")
@click.option("--private-room", is_flag=True, help="Has private room (個室)")
@click.option("--non-smoking", is_flag=True, help="Non-smoking (禁煙)")
@click.option("--lunch", is_flag=True, help="Lunch available (ランチ)")
@click.option("--reservable", is_flag=True, help="Online reservation (ネット予約可)")
@click.option("--all-you-can-drink", is_flag=True, help="All-you-can-drink (飲み放題)")
@click.option("--all-you-can-eat", is_flag=True, help="All-you-can-eat (食べ放題)")
@click.option("--card-ok", is_flag=True, help="Card accepted (カード可)")
@click.option("--parking", is_flag=True, help="Has parking (駐車場)")
@click.option("--kids-ok", is_flag=True, help="Kids welcome (子供可)")
@click.option("--sunday-open", is_flag=True, help="Open on Sunday (日曜営業)")
@click.option("--solo", is_flag=True, help="Solo-friendly (一人で入りやすい)")
@click.option("--date", is_flag=True, help="Good for dates (デート向け)")
@click.option("--counter", is_flag=True, help="Has counter seats (カウンター席)")
@click.option("--tatami", is_flag=True, help="Has tatami seating (座敷)")
@click.option("--limit", "-n", default=20, help="Max results to show")
@click.option("--sort", "-s", type=click.Choice(["trend", "rating", "reviews"]), default="trend",
              help="Sort order: trend (default), rating (highest first), reviews (most reviews)")
def search(
    query: str | None,
    area: str | None,
    genre: str | None,
    private_room: bool,
    non_smoking: bool,
    lunch: bool,
    reservable: bool,
    all_you_can_drink: bool,
    all_you_can_eat: bool,
    card_ok: bool,
    parking: bool,
    kids_ok: bool,
    sunday_open: bool,
    solo: bool,
    date: bool,
    counter: bool,
    tatami: bool,
    limit: int,
    sort: str,
):
    """Search for restaurants.

    Examples:
        tabelog search "sushi"
        tabelog search --genre ramen --area tokyo
        tabelog search "yakitori" --private-room --non-smoking
        tabelog search --lunch --solo -n 10
    """
    # Build filter list from flags
    filters = []
    if private_room:
        filters.append("private_room")
    if non_smoking:
        filters.append("non_smoking")
    if lunch:
        filters.append("lunch")
    if reservable:
        filters.append("reservable")
    if all_you_can_drink:
        filters.append("all_you_can_drink")
    if all_you_can_eat:
        filters.append("all_you_can_eat")
    if card_ok:
        filters.append("card_ok")
    if parking:
        filters.append("parking")
    if kids_ok:
        filters.append("kids_ok")
    if sunday_open:
        filters.append("sunday_open")
    if solo:
        filters.append("solo")
    if date:
        filters.append("date")
    if counter:
        filters.append("counter")
    if tatami:
        filters.append("tatami")

    try:
        results = client.search(
            query=query,
            area=area,
            genre=genre,
            filters=filters if filters else None,
            sort=sort,
        )
    except ValueError as e:
        click.echo(f"Error: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Error searching: {e}", err=True)
        raise SystemExit(1)

    if not results:
        click.echo("No restaurants found.")
        return

    title = "Search results"
    if query:
        title += f" for '{query}'"
    if genre:
        title += f" [{genre}]"
    if area:
        title += f" in {area}"

    click.echo(f"# {title}\n")
    for i, r in enumerate(results[:limit], 1):
        click.echo(f"{i}. **{r.name}** ({r.rating})")
        click.echo(f"   {r.area} | {r.cuisine}")
        if r.description:
            click.echo(f"   {r.description}")
        stats = []
        if r.review_count:
            stats.append(f"{r.review_count} reviews")
        if r.save_count:
            stats.append(f"{r.save_count} saves")
        if stats:
            click.echo(f"   📊 {' | '.join(stats)}")
        click.echo(f"   ID: `{r.id}`")
        click.echo()


@main.command()
@click.argument("region", required=False)
def areas(region: str | None):
    """List available areas for a region.

    Examples:
        tabelog areas tokyo     # List areas in Tokyo
        tabelog areas osaka     # List areas in Osaka
    """
    if not region:
        click.echo("Usage: tabelog areas <region>")
        click.echo("\nExamples: tokyo, osaka, kyoto, fukuoka, hokkaido")
        return

    try:
        area_list = client.get_areas(region)
    except Exception as e:
        click.echo(f"Error fetching areas: {e}", err=True)
        raise SystemExit(1)

    if not area_list:
        click.echo(f"No areas found for region: {region}")
        return

    click.echo(f"# Areas in {region}\n")
    for a in area_list:
        click.echo(f"- {a.name} (`{a.code}`)")


@main.command()
def genres():
    """List all available cuisine types (genres).

    Examples:
        tabelog genres
    """
    genre_list = client.list_genres()

    click.echo("# Available genres\n")
    for slug, ja, en in genre_list:
        click.echo(f"- `{slug}` - {ja} ({en})")


@main.command()
@click.argument("restaurant_id")
def info(restaurant_id: str):
    """Get detailed info for a restaurant.

    Examples:
        tabelog info 13002251
    """
    try:
        details = client.get_info(restaurant_id)
    except Exception as e:
        click.echo(f"Error fetching info: {e}", err=True)
        raise SystemExit(1)

    if not details:
        click.echo(f"Could not find restaurant with ID: {restaurant_id}", err=True)
        raise SystemExit(1)

    click.echo(f"# {details.name}\n")
    click.echo(f"**Rating:** {details.rating}")
    if details.cuisine:
        click.echo(f"**Cuisine:** {details.cuisine}")
    if details.address:
        click.echo(f"**Address:** {details.address}")
    if details.phone:
        click.echo(f"**Phone:** {details.phone}")
    if details.price_lunch or details.price_dinner:
        click.echo(f"**Price:** Lunch {details.price_lunch or 'N/A'} | Dinner {details.price_dinner or 'N/A'}")
    if details.hours:
        click.echo(f"**Hours:** {details.hours}")

    # Reservation info
    click.echo(f"\n## Reservations")
    if details.reservable:
        click.echo("**Online Booking:** Available ✓")
    else:
        click.echo("**Online Booking:** Not available")
    if details.reservation_status:
        click.echo(f"**Status:** {details.reservation_status}")

    # Courses
    if details.courses:
        click.echo(f"\n## Courses ({len(details.courses)})")
        for c in details.courses:
            items = f" ({c.num_items})" if c.num_items else ""
            click.echo(f"- {c.name}: ¥{c.price}{items}")

    # Facilities
    click.echo("\n## Facilities")
    if details.seats:
        click.echo(f"**Seats:** {details.seats}")
    if details.private_room:
        click.echo(f"**Private Room:** {details.private_room}")
    if details.smoking:
        click.echo(f"**Smoking:** {details.smoking}")
    if details.parking:
        click.echo(f"**Parking:** {details.parking}")

    # Other info
    if details.access or details.service_charge or details.payment_methods:
        click.echo("\n## Other Info")
        if details.access:
            click.echo(f"**Access:** {details.access}")
        if details.service_charge:
            click.echo(f"**Service Charge:** {details.service_charge}")
        if details.payment_methods:
            click.echo(f"**Payment:** {details.payment_methods}")

    click.echo(f"\n**URL:** {details.url}")


@main.command()
@click.argument("restaurant_id", required=False)
@click.option("--url", "-u", help="Fetch by URL instead of ID")
@click.option("--page", "-p", default=1, help="Starting page number (default: 1)")
@click.option("--pages", default=1, help="Number of pages to fetch (default: 1)")
def reviews(restaurant_id: str | None, url: str | None, page: int, pages: int):
    """Fetch reviews for a restaurant.

    Examples:
        tabelog reviews 13002251
        tabelog reviews 13002251 --pages 3       # Fetch 3 pages
        tabelog reviews 13002251 --page 2        # Start from page 2
        tabelog reviews --url "https://tabelog.com/tokyo/..."
    """
    if not restaurant_id and not url:
        click.echo("Error: Provide either a restaurant ID or --url", err=True)
        raise SystemExit(1)

    try:
        name, rating, review_list = client.get_reviews(
            restaurant_id=restaurant_id,
            url=url,
            page=page,
            max_pages=pages,
        )
    except Exception as e:
        click.echo(f"Error fetching reviews: {e}", err=True)
        raise SystemExit(1)

    page_info = f"page {page}" if pages == 1 else f"pages {page}-{page + pages - 1}"
    click.echo(f"# {name} (Rating: {rating}) - {page_info}\n")

    if not review_list:
        click.echo("No reviews found.")
        return

    for i, r in enumerate(review_list, 1):
        click.echo(f"## Review {i} ({r.rating})")
        if r.title:
            click.echo(f"**{r.title}**")
        if r.visit_date:
            click.echo(f"*{r.visit_date}*")
        if r.body:
            click.echo(f"\n{r.body}")
        click.echo()


if __name__ == "__main__":
    main()
