# Tabelog MCP Server

An MCP server and CLI for searching [Tabelog](https://tabelog.com), Japan's largest restaurant review site.

Tabelog ratings are notoriously strict - a 3.5+ is excellent, 4.0+ is exceptional. Most quality restaurants score 3.0-3.8.

## Quick Start

### Deploy to FastMCP Cloud

1. Go to [fastmcp.cloud](https://fastmcp.cloud) and sign in with GitHub
2. Create a new project pointing to this repo
3. Set entrypoint to `tabelog/mcp_server.py:mcp`
4. Your server will be live at `https://your-project.fastmcp.app/mcp`

### Run Locally

```bash
# Install
uv pip install -e .

# Run MCP server
fastmcp run tabelog/mcp_server.py:mcp

# Or use the CLI
tabelog search --area tokyo --genre ramen
```

## MCP Tools

| Tool | Description |
|------|-------------|
| `search_restaurants` | Search by area, genre, price, filters |
| `get_restaurant_info` | Get details (hours, address, courses) |
| `get_reviews` | Fetch user reviews |
| `get_restaurant_info_batch` | Get details for multiple restaurants (parallel) |
| `get_reviews_batch` | Fetch reviews for multiple restaurants (parallel) |
| `get_areas` | List neighborhoods for a region |
| `list_genres` | List cuisine types |
| `list_available_filters` | List search filters |
| `list_price_tiers` | List budget filter options |

### Example Usage

```
Search for ramen in Tokyo:
  search_restaurants(area="tokyo", genre="ramen")

High-end sushi dinner in Ginza (¥20,000+):
  search_restaurants(area="tokyo/A1301", genre="sushi", meal_type="dinner", price_min=20000)

Solo-friendly counter seats:
  search_restaurants(area="tokyo", filters="solo,counter")
```

## CLI Commands

```bash
# Search restaurants
tabelog search "銀座" --genre sushi --area tokyo
tabelog search --genre ramen --solo --lunch

# Get restaurant details
tabelog info 13002251

# Read reviews
tabelog reviews 13002251 --pages 3

# List areas/genres
tabelog areas tokyo
tabelog genres
```

### Search Filters

`--private-room` `--non-smoking` `--lunch` `--reservable` `--solo` `--date` `--counter` `--tatami` `--card-ok` `--parking` `--kids-ok` `--sunday-open` `--all-you-can-drink` `--all-you-can-eat`

## License

MIT
