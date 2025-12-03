"""CLI interface for Tabelog Explorer."""

import click

from . import __version__
from .areas import format_areas_list, get_area_code
from .scraper import get_restaurant_info, get_reviews, search_restaurants


@click.group()
@click.version_option(version=__version__)
def main():
    """Tabelog Explorer - Browse and search Japanese restaurant reviews."""
    pass


@main.command()
@click.argument("query")
@click.option("--area", "-a", help="Filter by area (e.g., tokyo/ginza)")
@click.option("--limit", "-n", default=20, help="Max results to show")
def search(query: str, area: str | None, limit: int):
    """Search for restaurants by keyword.

    Examples:
        tabelog search "sushi"
        tabelog search "ramen" --area tokyo
        tabelog search "yakitori ginza" -n 10
    """
    try:
        results = search_restaurants(query, area)
    except Exception as e:
        click.echo(f"Error searching: {e}", err=True)
        raise SystemExit(1)

    if not results:
        click.echo("No restaurants found.")
        return

    click.echo(f"# Search results for '{query}'\n")
    for i, r in enumerate(results[:limit], 1):
        click.echo(f"{i}. **{r.name}** ({r.rating})")
        click.echo(f"   {r.area} | {r.cuisine}")
        click.echo(f"   ID: `{r.id}`")
        click.echo()


@main.command()
@click.argument("region", required=False)
def areas(region: str | None):
    """List available regions and areas.

    Examples:
        tabelog areas           # List all regions
        tabelog areas tokyo     # List areas in Tokyo
    """
    output = format_areas_list(region)
    click.echo(output)


@main.command()
@click.argument("restaurant_id")
def info(restaurant_id: str):
    """Get detailed info for a restaurant.

    Examples:
        tabelog info 13002251
    """
    try:
        details = get_restaurant_info(restaurant_id)
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
    if details.price_lunch or details.price_dinner:
        click.echo(f"**Price:** Lunch {details.price_lunch or 'N/A'} | Dinner {details.price_dinner or 'N/A'}")
    if details.hours:
        click.echo(f"**Hours:** {details.hours}")
    click.echo(f"\n**URL:** {details.url}")


@main.command()
@click.argument("restaurant_id", required=False)
@click.option("--url", "-u", help="Fetch by URL instead of ID")
def reviews(restaurant_id: str | None, url: str | None):
    """Fetch reviews for a restaurant.

    Examples:
        tabelog reviews 13002251
        tabelog reviews --url "https://tabelog.com/tokyo/..."
    """
    if not restaurant_id and not url:
        click.echo("Error: Provide either a restaurant ID or --url", err=True)
        raise SystemExit(1)

    try:
        name, rating, review_list = get_reviews(restaurant_id=restaurant_id, url=url)
    except Exception as e:
        click.echo(f"Error fetching reviews: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"# {name} (Rating: {rating})\n")

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
