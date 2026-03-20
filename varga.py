from constants import RASHI_NAMES, PLANET_NAMES, ZODIAC_LORDS

VARGA_NAMES = {
    "D1": "Rashi (Birth Chart)",
    "D2": "Hora (Wealth)",
    "D3": "Drekkana (Siblings)",
    "D4": "Chaturthamsha (Fortune)",
    "D7": "Saptamsha (Children)",
    "D9": "Navamsa (Spouse & Dharma)",
    "D10": "Dashamsha (Career)",
    "D12": "Dwadashamsha (Parents)",
    "D16": "Shodashamsha (Vehicles)",
    "D20": "Vimshamsha (Spiritual)",
    "D24": "Chaturvimshamsha (Education)",
    "D27": "Saptavimshamsha (Strength)",
    "D30": "Trimshamsha (Misfortune)",
    "D40": "Khavedamsha (Maternal)",
    "D45": "Akshavedamsha (Paternal)",
    "D60": "Shashtiamsha (All Matters)",
}
VALID_VARGAS = list(VARGA_NAMES.keys())


def format_varga(chart_data, varga_key):
    """
    Format a divisional chart table.
    Varga graha data only has: rashi, degree, speed, longitude (no nakshatra).
    Table columns: Planet | House | Zodiac | Sign Lord | Degree
    """
    varga_data = chart_data.get("chart", {}).get("varga", {}).get(varga_key)
    if not varga_data:
        return f"No data for {varga_key}. Ensure this varga was requested from the API."

    graha = varga_data.get("graha", {})
    lagna_data = varga_data.get("lagna", {})
    ref_rashi = lagna_data.get("Lg", {}).get("rashi")
    if ref_rashi is None:
        return f"No ascendant data for {varga_key}."

    asc_name = RASHI_NAMES.get(ref_rashi, "?")
    varga_title = VARGA_NAMES.get(varga_key, varga_key)

    W = {"planet": 9, "house": 2, "zodiac": 11, "sign_lord": 9, "degree": 8}

    def row(planet, house, zodiac, sign_lord, degree):
        return (
            f"{planet:<{W['planet']}} {house:>{W['house']}} "
            f"{zodiac:<{W['zodiac']}} {sign_lord:<{W['sign_lord']}} "
            f"{degree:>{W['degree']}}"
        )

    header_row = row("Planet", "Hs", "Zodiac", "Sign Lord", "Degree")
    separator = "-" * len(header_row)
    rows = [varga_title, f"Asc is {asc_name}", "```", header_row, separator]

    # Ascendant row
    lg = lagna_data.get("Lg", {})
    rows.append(row("Asc", "1", RASHI_NAMES.get(ref_rashi, "—"), ZODIAC_LORDS.get(ref_rashi, "—"), f"{lg.get('degree', 0):.2f}°"))
    rows.append(separator)

    for key, full_name in PLANET_NAMES.items():
        planet = graha.get(key)
        if not planet:
            continue
        rashi_num = planet.get("rashi")
        if rashi_num is None:
            continue
        house = (rashi_num - ref_rashi) % 12 + 1
        rows.append(row(full_name, str(house), RASHI_NAMES.get(rashi_num, "—"), ZODIAC_LORDS.get(rashi_num, "—"), f"{planet.get('degree', 0):.2f}°"))

    rows.append("```")
    return "\n".join(rows)
