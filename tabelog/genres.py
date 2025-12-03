"""
Tabelog Genre/Cuisine Categories (ジャンル)

URL pattern: https://tabelog.com/rstLst/{slug}/
Area-specific: https://tabelog.com/{area}/rstLst/{slug}/
"""

# Popular genres with Japanese name, English name, and URL slug
GENRES = {
    # Japanese cuisine
    "ramen": {"ja": "ラーメン", "en": "Ramen"},
    "sushi": {"ja": "寿司", "en": "Sushi"},
    "izakaya": {"ja": "居酒屋", "en": "Izakaya"},
    "yakitori": {"ja": "焼き鳥", "en": "Yakitori"},
    "yakiniku": {"ja": "焼肉", "en": "Yakiniku"},
    "tempura": {"ja": "天ぷら", "en": "Tempura"},
    "tonkatsu": {"ja": "とんかつ", "en": "Tonkatsu"},
    "udon": {"ja": "うどん", "en": "Udon"},
    "soba": {"ja": "そば", "en": "Soba"},
    "washoku": {"ja": "和食", "en": "Japanese (Washoku)"},
    "japanese": {"ja": "日本料理", "en": "Japanese Cuisine"},
    "unagi": {"ja": "うなぎ", "en": "Eel"},
    "seafood": {"ja": "海鮮・魚介", "en": "Seafood"},
    "gyouza": {"ja": "餃子", "en": "Gyoza"},
    "kushiage": {"ja": "串揚げ", "en": "Kushiage"},
    "okonomiyaki": {"ja": "お好み焼き", "en": "Okonomiyaki"},
    "monjya": {"ja": "もんじゃ焼き", "en": "Monjayaki"},
    "okinawafood": {"ja": "沖縄料理", "en": "Okinawan"},

    # Hot pot / Nabe
    "nabe": {"ja": "鍋", "en": "Hot Pot"},
    "syabusyabu": {"ja": "しゃぶしゃぶ", "en": "Shabu-shabu"},
    "motsu": {"ja": "もつ鍋", "en": "Motsu Nabe"},
    "horumon": {"ja": "ホルモン", "en": "Offal"},

    # International
    "italian": {"ja": "イタリアン", "en": "Italian"},
    "french": {"ja": "フレンチ", "en": "French"},
    "chinese": {"ja": "中華料理", "en": "Chinese"},
    "korea": {"ja": "韓国料理", "en": "Korean"},
    "thai": {"ja": "タイ料理", "en": "Thai"},
    "spain": {"ja": "スペイン料理", "en": "Spanish"},
    "yoshoku": {"ja": "洋食", "en": "Western-style Japanese"},

    # Western dishes
    "steak": {"ja": "ステーキ", "en": "Steak"},
    "hamburger": {"ja": "ハンバーガー", "en": "Hamburger"},
    "hamburgersteak": {"ja": "ハンバーグ", "en": "Hamburg Steak"},
    "pasta": {"ja": "パスタ", "en": "Pasta"},
    "pizza": {"ja": "ピザ", "en": "Pizza"},
    "curry": {"ja": "カレー", "en": "Curry"},
    "bistro": {"ja": "ビストロ", "en": "Bistro"},

    # Cafe & Sweets
    "cafe": {"ja": "カフェ", "en": "Cafe"},
    "kissaten": {"ja": "喫茶店", "en": "Coffee Shop"},
    "pan": {"ja": "パン", "en": "Bakery"},
    "cake": {"ja": "ケーキ", "en": "Cake"},
    "sweets": {"ja": "スイーツ", "en": "Sweets"},
    "tapioca": {"ja": "タピオカ", "en": "Bubble Tea"},

    # Dining styles
    "bar": {"ja": "バー・お酒", "en": "Bar"},
    "teishoku": {"ja": "食堂", "en": "Cafeteria"},
    "viking": {"ja": "ビュッフェ", "en": "Buffet"},
    "ryokan": {"ja": "料理旅館", "en": "Ryokan"},

    # Special
    "lunch": {"ja": "ランチ", "en": "Lunch"},
}

# Category codes (broader categories)
CATEGORY_CODES = {
    "RC": {"ja": "レストラン", "en": "Restaurant"},
    "SC": {"ja": "カフェ・スイーツ", "en": "Cafe/Sweets"},
    "YC": {"ja": "料理旅館", "en": "Ryokan/Auberge"},
    "ZZ": {"ja": "その他", "en": "Other"},
}


def get_genre_url(slug: str, area: str | None = None) -> str:
    """Build URL for a genre search."""
    if area:
        return f"https://tabelog.com/{area}/rstLst/{slug}/"
    return f"https://tabelog.com/rstLst/{slug}/"


def list_genres() -> list[tuple[str, str, str]]:
    """Return list of (slug, japanese_name, english_name) tuples."""
    return [(slug, info["ja"], info["en"]) for slug, info in GENRES.items()]
