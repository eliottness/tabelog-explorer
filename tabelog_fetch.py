#!/usr/bin/env python3
"""Simple CLI to fetch Tabelog restaurant reviews."""

import re
import sys
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "ja,en;q=0.9",
}


def fetch_reviews(url: str) -> str:
    """Fetch and parse reviews from a Tabelog restaurant page."""
    # Ensure we're on the reviews page
    if "/dtlrvwlst/" not in url:
        # Convert main page URL to reviews page
        url = url.rstrip("/") + "/dtlrvwlst/"

    response = requests.get(url, headers=HEADERS, timeout=30)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "lxml")

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

    # Build markdown output
    output = [f"# {restaurant_name} (Rating: {overall_rating})\n"]

    # Find all review items
    reviews = soup.select(".rvw-item")

    if not reviews:
        output.append("No reviews found on this page.\n")
        return "\n".join(output)

    for i, review in enumerate(reviews, 1):
        # Get individual review rating (encoded in class like c-rating-v3--val35 = 3.5)
        review_rating = "N/A"
        rating_elem = review.select_one(".rvw-item__ratings-total")
        if rating_elem:
            classes = rating_elem.get("class", [])
            for cls in classes:
                match = re.search(r"c-rating-v3--val(\d+)", cls)
                if match:
                    val = int(match.group(1))
                    review_rating = f"{val / 10:.1f}"
                    break

        # Get review title
        title_elem = review.select_one(".rvw-item__title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Get review body text
        body_elem = review.select_one(".rvw-item__rvw-comment")
        if body_elem:
            # Remove "read more" links and clean up
            for a in body_elem.select("a"):
                a.decompose()
            body = body_elem.get_text(strip=True)
        else:
            body = ""

        # Get visit date if available
        date_elem = review.select_one(".rvw-item__visit-date")
        visit_date = date_elem.get_text(strip=True) if date_elem else ""

        output.append(f"## Review {i} ({review_rating})")
        if title:
            output.append(f"**{title}**")
        if visit_date:
            output.append(f"*{visit_date}*")
        if body:
            output.append(f"\n{body}")
        output.append("")

    return "\n".join(output)


def main():
    if len(sys.argv) < 2:
        print("Usage: tabelog-fetch <tabelog-url>", file=sys.stderr)
        print("Example: tabelog-fetch https://tabelog.com/tokyo/A1301/A130101/13000001/", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]

    if "tabelog.com" not in url:
        print("Error: Please provide a valid Tabelog URL", file=sys.stderr)
        sys.exit(1)

    try:
        result = fetch_reviews(url)
        print(result)
    except requests.RequestException as e:
        print(f"Error fetching URL: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
