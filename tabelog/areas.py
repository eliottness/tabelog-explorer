"""Area and region data for Tabelog."""

# Major regions and their prefectures/areas
REGIONS = {
    "tokyo": {
        "name": "Tokyo",
        "code": "tokyo",
        "areas": {
            # Central/Business
            "ginza": {"name": "Ginza", "code": "A1301/A130101"},
            "shinbashi": {"name": "Shinbashi", "code": "A1301/A130103"},
            "yurakucho": {"name": "Yurakucho", "code": "A1301/A130102"},
            "marunouchi": {"name": "Marunouchi", "code": "A1302/A130201"},
            "nihonbashi": {"name": "Nihonbashi", "code": "A1302/A130202"},
            "tokyo_station": {"name": "Tokyo Station", "code": "A1302/A130203"},
            # Shibuya/Harajuku area
            "shibuya": {"name": "Shibuya", "code": "A1303/A130301"},
            "ebisu": {"name": "Ebisu", "code": "A1303/A130302"},
            "daikanyama": {"name": "Daikanyama", "code": "A1303/A130303"},
            "harajuku": {"name": "Harajuku", "code": "A1306/A130601"},
            "omotesando": {"name": "Omotesando", "code": "A1306/A130603"},
            # Shinjuku area
            "shinjuku": {"name": "Shinjuku", "code": "A1304/A130401"},
            "kabukicho": {"name": "Kabukicho", "code": "A1304/A130402"},
            "yoyogi": {"name": "Yoyogi", "code": "A1304/A130403"},
            # Ikebukuro area
            "ikebukuro": {"name": "Ikebukuro", "code": "A1305/A130501"},
            # Aoyama/Akasaka area
            "aoyama": {"name": "Aoyama", "code": "A1306/A130602"},
            "roppongi": {"name": "Roppongi", "code": "A1307/A130701"},
            "azabu": {"name": "Azabu", "code": "A1307/A130702"},
            "akasaka": {"name": "Akasaka", "code": "A1308/A130801"},
            "toranomon": {"name": "Toranomon", "code": "A1308/A130802"},
            # Meguro area
            "nakameguro": {"name": "Nakameguro", "code": "A1317/A131701"},
            "meguro": {"name": "Meguro", "code": "A1317/A131702"},
            "gotanda": {"name": "Gotanda", "code": "A1316/A131601"},
            # East Tokyo
            "ueno": {"name": "Ueno", "code": "A1311/A131101"},
            "asakusa": {"name": "Asakusa", "code": "A1311/A131102"},
            "akihabara": {"name": "Akihabara", "code": "A1310/A131001"},
            "kanda": {"name": "Kanda", "code": "A1310/A131002"},
            "ryogoku": {"name": "Ryogoku", "code": "A1312/A131201"},
            # Waterfront
            "odaiba": {"name": "Odaiba", "code": "A1313/A131301"},
            "tsukiji": {"name": "Tsukiji", "code": "A1313/A131302"},
            "toyosu": {"name": "Toyosu", "code": "A1313/A131303"},
            # West Tokyo
            "kichijoji": {"name": "Kichijoji", "code": "A1320/A132001"},
            "nakano": {"name": "Nakano", "code": "A1319/A131901"},
            "shimokitazawa": {"name": "Shimokitazawa", "code": "A1318/A131801"},
        },
    },
    "osaka": {
        "name": "Osaka",
        "code": "osaka",
        "areas": {
            "umeda": {"name": "Umeda", "code": "A2701/A270101"},
            "namba": {"name": "Namba", "code": "A2702/A270201"},
            "shinsaibashi": {"name": "Shinsaibashi", "code": "A2702/A270202"},
            "dotonbori": {"name": "Dotonbori", "code": "A2702/A270203"},
            "tennoji": {"name": "Tennoji", "code": "A2703/A270301"},
            "kitashinchi": {"name": "Kitashinchi", "code": "A2701/A270102"},
        },
    },
    "kyoto": {
        "name": "Kyoto",
        "code": "kyoto",
        "areas": {
            "gion": {"name": "Gion", "code": "A2601/A260101"},
            "kawaramachi": {"name": "Kawaramachi", "code": "A2601/A260102"},
            "pontocho": {"name": "Pontocho", "code": "A2601/A260103"},
            "kiyamachi": {"name": "Kiyamachi", "code": "A2601/A260104"},
            "arashiyama": {"name": "Arashiyama", "code": "A2602/A260201"},
        },
    },
    "fukuoka": {
        "name": "Fukuoka",
        "code": "fukuoka",
        "areas": {
            "hakata": {"name": "Hakata", "code": "A4001/A400101"},
            "tenjin": {"name": "Tenjin", "code": "A4001/A400102"},
            "nakasu": {"name": "Nakasu", "code": "A4001/A400103"},
        },
    },
    "hokkaido": {
        "name": "Hokkaido",
        "code": "hokkaido",
        "areas": {
            "sapporo": {"name": "Sapporo", "code": "A0101/A010101"},
            "susukino": {"name": "Susukino", "code": "A0101/A010102"},
            "odori": {"name": "Odori", "code": "A0101/A010103"},
        },
    },
}


def get_regions() -> list[str]:
    """Get list of available regions."""
    return list(REGIONS.keys())


def get_areas(region: str) -> dict[str, dict] | None:
    """Get areas for a region."""
    if region.lower() in REGIONS:
        return REGIONS[region.lower()]["areas"]
    return None


def get_area_code(region: str, area: str) -> str | None:
    """Get the Tabelog area code for a region/area combo."""
    region_data = REGIONS.get(region.lower())
    if not region_data:
        return None
    area_data = region_data["areas"].get(area.lower())
    if not area_data:
        return None
    return f"{region_data['code']}/{area_data['code']}"


def format_areas_list(region: str | None = None) -> str:
    """Format areas as a readable list."""
    lines = []

    if region:
        region_data = REGIONS.get(region.lower())
        if not region_data:
            return f"Unknown region: {region}"

        lines.append(f"# Areas in {region_data['name']}\n")
        for key, area in region_data["areas"].items():
            lines.append(f"- **{key}** ({area['name']})")
    else:
        lines.append("# Available Regions\n")
        for key, region_data in REGIONS.items():
            area_count = len(region_data["areas"])
            lines.append(f"- **{key}** ({region_data['name']}) - {area_count} areas")
        lines.append("\nUse `tabelog areas <region>` to see areas within a region.")

    return "\n".join(lines)
