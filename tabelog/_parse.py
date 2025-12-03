"""HTML parsing functions for Tabelog pages."""

import re

from bs4 import BeautifulSoup

from .models import Area, Restaurant, RestaurantDetail, Review


def _extract_rating_from_class(classes: list[str]) -> str:
    """Extract rating from CSS class like c-rating-v3--val35 = 3.5."""
    for cls in classes:
        match = re.search(r"c-rating-v3--val(\d+)", cls)
        if match:
            val = int(match.group(1))
            return f"{val / 10:.1f}"
    return "N/A"


def parse_search_results(soup: BeautifulSoup) -> list[Restaurant]:
    """Parse restaurant search results page."""
    restaurants = []

    for item in soup.select(".list-rst"):
        link_elem = item.select_one(".list-rst__rst-name-target")
        if not link_elem:
            continue

        url = link_elem.get("href", "")
        id_match = re.search(r"/(\d+)/?$", url)
        rst_id = id_match.group(1) if id_match else ""

        name = link_elem.get_text(strip=True)

        rating_elem = item.select_one(".c-rating__val")
        rating = rating_elem.get_text(strip=True) if rating_elem else "N/A"

        area_elem = item.select_one(".list-rst__area-genre")
        area_text = ""
        cuisine = ""
        if area_elem:
            parts = area_elem.get_text(strip=True).split("/")
            area_text = parts[0].strip() if parts else ""
            cuisine = parts[1].strip() if len(parts) > 1 else ""

        restaurants.append(Restaurant(
            id=rst_id,
            name=name,
            rating=rating,
            area=area_text,
            cuisine=cuisine,
            url=url,
        ))

    return restaurants


def parse_restaurant_detail(soup: BeautifulSoup, restaurant_id: str, url: str) -> RestaurantDetail | None:
    """Parse restaurant detail page."""
    name_elem = soup.select_one("h2.display-name a")
    if not name_elem:
        name_elem = soup.select_one("h2.display-name")
    if not name_elem:
        return None

    name = name_elem.get_text(strip=True)

    # Rating
    rating_elem = soup.select_one(".rdheader-rating__score-val-dtl")
    if not rating_elem:
        rating_elem = soup.select_one(".rdheader-rating__score-val")
    rating = rating_elem.get_text(strip=True) if rating_elem else "N/A"

    # Address
    address_elem = soup.select_one(".rstinfo-table__address")
    address = address_elem.get_text(strip=True) if address_elem else ""

    # Cuisine/genre
    genre_elem = soup.select_one(".rdheader-subinfo__genre")
    cuisine = genre_elem.get_text(strip=True) if genre_elem else ""

    # Price (lunch/dinner)
    price_lunch = ""
    price_dinner = ""
    budget_elems = soup.select(".rdheader-budget__price")
    for elem in budget_elems:
        text = elem.get_text(strip=True)
        label = elem.find_previous_sibling()
        if label and "昼" in label.get_text():
            price_lunch = text
        elif label and "夜" in label.get_text():
            price_dinner = text

    # Hours - find th containing 営業時間 and get sibling td
    hours = ""
    for th in soup.select("th"):
        if "営業時間" in th.get_text():
            td = th.find_next_sibling("td")
            if td:
                hours = td.get_text(strip=True)
            break

    return RestaurantDetail(
        id=restaurant_id,
        name=name,
        rating=rating,
        address=address,
        cuisine=cuisine,
        price_lunch=price_lunch,
        price_dinner=price_dinner,
        hours=hours,
        url=url,
    )


def parse_reviews(soup: BeautifulSoup) -> tuple[str, str, list[Review]]:
    """Parse reviews page. Returns (restaurant_name, overall_rating, reviews)."""
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

    # Parse reviews
    reviews = []
    for review_elem in soup.select(".rvw-item"):
        # Rating from class
        review_rating = "N/A"
        rating_p = review_elem.select_one(".rvw-item__ratings-total")
        if rating_p:
            classes = rating_p.get("class", [])
            review_rating = _extract_rating_from_class(classes)

        # Title
        title_elem = review_elem.select_one(".rvw-item__title")
        title = title_elem.get_text(strip=True) if title_elem else ""

        # Body
        body_elem = review_elem.select_one(".rvw-item__rvw-comment")
        if body_elem:
            for a in body_elem.select("a"):
                a.decompose()
            body = body_elem.get_text(strip=True)
        else:
            body = ""

        # Visit date
        date_elem = review_elem.select_one(".rvw-item__visit-date")
        visit_date = date_elem.get_text(strip=True) if date_elem else ""

        reviews.append(Review(
            rating=review_rating,
            title=title,
            body=body,
            visit_date=visit_date,
        ))

    return restaurant_name, overall_rating, reviews


def parse_areas(soup: BeautifulSoup, parent_code: str | None = None) -> list[Area]:
    """Parse area listing from region page."""
    areas = []

    # Areas are typically in links with patterns like /tokyo/A1301/
    for link in soup.select("a[href*='/A']"):
        href = link.get("href", "")
        # Match area codes like A1301, A130101
        match = re.search(r"/(A\d{4,6})/?", href)
        if match:
            code = match.group(1)
            name = link.get_text(strip=True)
            if name and code not in [a.code for a in areas]:
                areas.append(Area(code=code, name=name, parent_code=parent_code))

    return areas
