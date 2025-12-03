"""Data models for Tabelog API."""

from dataclasses import dataclass, field


@dataclass
class Course:
    """Restaurant course/plan."""

    name: str
    price: str
    num_items: str  # e.g., "6品"


@dataclass
class ReviewSnippet:
    """A brief review preview from search results."""

    title: str  # Review headline
    text: str  # Snippet of review text
    reviewer: str  # Reviewer name


@dataclass
class Restaurant:
    """Restaurant basic info from search results."""

    id: str
    name: str
    rating: str
    area: str
    cuisine: str
    url: str
    # Enriched data
    description: str = ""  # Promotional text
    review_count: int = 0  # Number of reviews
    save_count: int = 0  # Number of people who saved it
    # Price range
    price_lunch: str = ""
    price_dinner: str = ""
    # Featured review
    review_snippet: ReviewSnippet | None = None


@dataclass
class RestaurantDetail:
    """Detailed restaurant info from restaurant page."""

    id: str
    name: str
    rating: str
    address: str
    cuisine: str
    price_lunch: str
    price_dinner: str
    hours: str
    url: str
    # Reservation info
    phone: str = ""
    reservable: bool = False  # Online booking available
    reservation_status: str = ""  # e.g., "予約可"
    courses: list[Course] = field(default_factory=list)
    # Facilities
    seats: str = ""
    private_room: str = ""
    smoking: str = ""
    parking: str = ""
    # Other
    access: str = ""  # Transportation info
    service_charge: str = ""
    payment_methods: str = ""


@dataclass
class Review:
    """A single review."""
    rating: str
    title: str
    body: str
    visit_date: str


@dataclass
class Area:
    """Area/region info."""
    code: str
    name: str
    parent_code: str | None = None
