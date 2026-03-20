from constants import (
    RASHI_NAMES, PLANET_NAMES, ZODIAC_LORDS, NAKSHATRA_LORDS,
    RASHI_AVASTHA_LABELS, BALADI_LABELS, JAGRADI_LABELS,
    BHAVA_CHAR_LABELS, RELATION_LABELS,
    KARAKA_NAMES, KARAKA_PLANETS,
)


# ---------------------------------------------------------------------------
# House calculation
# ---------------------------------------------------------------------------

def whole_sign_house(planet_rashi, reference_rashi):
    """Return house number (1-12) using whole-sign system from a reference rashi."""
    return (planet_rashi - reference_rashi) % 12 + 1


# ---------------------------------------------------------------------------
# Chart table
# ---------------------------------------------------------------------------

_W = {"planet": 9, "house": 2, "zodiac": 11, "nakshatra": 18,
      "sign_lord": 8, "nak_lord": 8, "degree": 7}


def _table_row(planet, house, zodiac, nakshatra, sign_lord, nak_lord, degree):
    return (
        f"{planet:<{_W['planet']}} {house:>{_W['house']}} "
        f"{zodiac:<{_W['zodiac']}} {nakshatra:<{_W['nakshatra']}} "
        f"{sign_lord:<{_W['sign_lord']}} {nak_lord:<{_W['nak_lord']}} "
        f"{degree:>{_W['degree']}}"
    )


def format_chart(chart_data, reference="lagna"):
    """
    Format the chart as a monospace table inside a code block.
    reference: "lagna" | "sun" | "moon"
    """
    chart = chart_data.get("chart", {})
    graha = chart.get("graha", {})
    lagna = chart.get("lagna", {})

    if reference == "lagna":
        ref_rashi = lagna.get("Lg", {}).get("rashi")
        if ref_rashi is None:
            return "Could not determine Ascendant from chart data."
        header = f"Asc is {RASHI_NAMES.get(ref_rashi, f'Rashi {ref_rashi}')}"
    elif reference == "sun":
        ref_rashi = graha.get("Su", {}).get("rashi")
        if ref_rashi is None:
            return "Could not determine Sun sign from chart data."
        header = f"Sun is in {RASHI_NAMES.get(ref_rashi, f'Rashi {ref_rashi}')}"
    elif reference == "moon":
        ref_rashi = graha.get("Mo", {}).get("rashi")
        if ref_rashi is None:
            return "Could not determine Moon sign from chart data."
        header = f"Moon is in {RASHI_NAMES.get(ref_rashi, f'Rashi {ref_rashi}')}"
    else:
        return f"Unknown reference: {reference}"

    header_row = _table_row("Planet", "Hs", "Zodiac", "Nakshatra", "SignLord", "NakLord", "Degree")
    separator = "-" * len(header_row)
    rows = [header, "```", header_row, separator]

    if reference == "lagna":
        lg = lagna.get("Lg", {})
        lg_rashi = lg.get("rashi")
        if lg_rashi:
            nak_info = lg.get("nakshatra", {}) or {}
            nak_key = nak_info.get("key")
            rows.append(_table_row(
                "Asc", "1",
                RASHI_NAMES.get(lg_rashi, "—"),
                nak_info.get("name", "—"),
                ZODIAC_LORDS.get(lg_rashi, "—"),
                NAKSHATRA_LORDS.get(nak_key, "—") if nak_key else "—",
                f"{lg.get('degree', 0):.2f}°",
            ))
        rows.append(separator)

    for key, full_name in PLANET_NAMES.items():
        planet = graha.get(key)
        if not planet:
            continue
        rashi_num = planet.get("rashi")
        if rashi_num is None:
            continue
        nak_info = planet.get("nakshatra", {}) or {}
        nak_key = nak_info.get("key")
        rows.append(_table_row(
            full_name,
            str(whole_sign_house(rashi_num, ref_rashi)),
            RASHI_NAMES.get(rashi_num, "—"),
            nak_info.get("name", "—"),
            ZODIAC_LORDS.get(rashi_num, "—"),
            NAKSHATRA_LORDS.get(nak_key, "—") if nak_key else "—",
            f"{planet.get('degree', 0):.2f}°",
        ))

    rows.append("```")
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Planet detail
# ---------------------------------------------------------------------------

def format_planet_detail(chart_data, planet_key, chart_label, karaka_label=None):
    """Full detail block for a single planet."""
    chart = chart_data.get("chart", {})
    graha = chart.get("graha", {})
    lagna = chart.get("lagna", {})

    planet = graha.get(planet_key)
    if not planet:
        return f"No data for {PLANET_NAMES.get(planet_key, planet_key)}."

    full_name  = PLANET_NAMES[planet_key]
    rashi_num  = planet.get("rashi")
    zodiac     = RASHI_NAMES.get(rashi_num, "—")
    degree     = planet.get("degree", 0)
    longitude  = planet.get("longitude", 0)
    speed      = planet.get("speed", 0)

    ref_rashi = lagna.get("Lg", {}).get("rashi")
    house = whole_sign_house(rashi_num, ref_rashi) if ref_rashi and rashi_num else "?"

    nak_info  = planet.get("nakshatra") or {}
    nak_name  = nak_info.get("name", "—")
    nak_pada  = nak_info.get("pada", "—")
    nak_left  = nak_info.get("left")
    nak_key   = nak_info.get("key")
    nak_lord  = NAKSHATRA_LORDS.get(nak_key, "—") if nak_key else "—"

    sign_lord  = ZODIAC_LORDS.get(rashi_num, "—")
    disp_key   = planet.get("dispositor")
    dispositor = PLANET_NAMES.get(disp_key, disp_key or "—")
    rashi_avs  = planet.get("rashiAvastha", "")
    bhava_char = planet.get("bhavaCharacter", "")
    vargottama = planet.get("vargottama", False)
    astangata  = planet.get("astangata")
    yogakaraka = planet.get("yogakaraka", False)
    mrityu     = planet.get("mrityu", False)
    push_nav   = planet.get("pushkaraNavamsha", 0)
    push_bhaga = planet.get("pushkaraBhaga", False)

    avastha  = planet.get("avastha") or {}
    baladi   = avastha.get("baladi", "")
    jagradi  = avastha.get("jagradi", "")
    deeptadi = avastha.get("deeptadi") or []

    relations = planet.get("relation") or {}

    W = 16

    def line(label, value):
        return f"  {label:<{W}} {value}"

    title = f"{full_name} — {zodiac} {degree:.2f}° — House {house}"
    if karaka_label:
        title += f"  [{karaka_label}]"

    rows = [title, f"  Chart: {chart_label}", "```",
        "── Position ──────────────────────────────",
        line("Degree in Sign",  f"{degree:.4f}°"),
        line("Absolute Long.",  f"{longitude:.4f}°"),
        line("Speed",           f"{speed:+.4f}°/day  ({'retrograde' if speed < 0 else 'direct'})"),
        "",
        "── Nakshatra ─────────────────────────────",
        line("Name",            f"{nak_name}, Pada {nak_pada}"),
        line("Lord",            nak_lord),
        line("Degrees Left",    f"{nak_left:.2f}°" if nak_left is not None else "—"),
        "",
        "── Dignity ───────────────────────────────",
        line("Sign",            zodiac),
        line("Sign Lord",       sign_lord),
        line("Dispositor",      dispositor),
        line("Dignity",         RASHI_AVASTHA_LABELS.get(rashi_avs, rashi_avs.title() if rashi_avs else "—")),
        line("House Type",      BHAVA_CHAR_LABELS.get(bhava_char, bhava_char.title() if bhava_char else "—")),
        "",
        "── Avasthas ──────────────────────────────",
        line("Age State",       BALADI_LABELS.get(baladi, baladi.title() if baladi else "—")),
        line("Sleep State",     JAGRADI_LABELS.get(jagradi, jagradi.title() if jagradi else "—")),
        line("Luminosity",      ", ".join(d.title() for d in deeptadi) if deeptadi else "—"),
        "",
        "── Special States ────────────────────────",
        line("Vargottama",      "Yes ✦" if vargottama else "No"),
        line("Combust",         "Yes ✦" if astangata else "No"),
        line("Yogakaraka",      "Yes ✦" if yogakaraka else "No"),
        line("Mrityu Bhaga",    "Yes ✦" if mrityu else "No"),
        line("Pushkara Nav.",   "Yes ✦" if push_nav else "No"),
        line("Pushkara Bhaga",  "Yes ✦" if push_bhaga else "No"),
    ]

    if relations:
        rows += ["", "── Planetary Relations ───────────────────"]
        for pk, val in relations.items():
            if pk == planet_key or val is None:
                continue
            rows.append(line(PLANET_NAMES.get(pk, pk), RELATION_LABELS.get(val, str(val))))

    rows.append("```")
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Jaimini Karakas
# ---------------------------------------------------------------------------

def compute_karakas(chart_data):
    """
    Return list of (karaka_name, abbr, description, planet_name, degree)
    sorted from AK (highest degree) to DK (lowest degree).
    """
    graha = chart_data.get("chart", {}).get("graha", {})
    degrees = []
    for key in KARAKA_PLANETS:
        planet = graha.get(key)
        if not planet:
            continue
        deg = planet.get("degree")
        if deg is not None:
            degrees.append((key, deg))

    degrees.sort(key=lambda x: x[1], reverse=True)

    return [
        (*KARAKA_NAMES[i], PLANET_NAMES[key], deg)
        for i, (key, deg) in enumerate(degrees)
        if i < len(KARAKA_NAMES)
    ]


def format_karakas(chart_data, chart_name):
    karakas = compute_karakas(chart_data)
    if not karakas:
        return "No planetary data found."

    w_karaka, w_abbr, w_planet, w_degree, w_desc = 13, 3, 7, 7, 35

    def row(karaka, abbr, planet, degree, desc):
        return (
            f"{karaka:<{w_karaka}} {abbr:<{w_abbr}} {planet:<{w_planet}} "
            f"{degree:>{w_degree}} {desc}"
        )

    header_row = row("Karaka", "", "Planet", "Degree", "Signifies")
    separator = "-" * (w_karaka + 1 + w_abbr + 1 + w_planet + 1 + w_degree + 1 + w_desc)

    rows = [f"Jaimini Karakas — {chart_name}", "```", header_row, separator]
    for karaka, abbr, desc, planet, deg in karakas:
        rows.append(row(karaka, abbr, planet, f"{deg:.2f}°", desc))
    rows.append("```")
    return "\n".join(rows)


# ---------------------------------------------------------------------------
# Synastry
# ---------------------------------------------------------------------------

def get_aspect(lng1, lng2):
    diff = abs((lng1 - lng2) % 360)
    if diff > 180:
        diff = 360 - diff
    if diff <= 8:           return "Conjunction"
    if abs(diff - 60) <= 6: return "Sextile"
    if abs(diff - 90) <= 8: return "Square"
    if abs(diff - 120) <= 8:return "Trine"
    if abs(diff - 180) <= 8:return "Opposition"
    return "—"


_SW = {"planet": 9, "zod1": 11, "zod2": 11, "nak1": 18, "nak2": 18, "aspect": 11}


def _syn_row(planet, zod1, zod2, nak1, nak2, aspect):
    return (
        f"{planet:<{_SW['planet']}} {zod1:<{_SW['zod1']}} {zod2:<{_SW['zod2']}} "
        f"{nak1:<{_SW['nak1']}} {nak2:<{_SW['nak2']}} {aspect:<{_SW['aspect']}}"
    )


def format_synastry(data1, data2, name1, name2):
    c1, c2 = data1.get("chart", {}), data2.get("chart", {})
    g1, g2 = c1.get("graha", {}), c2.get("graha", {})
    l1, l2 = c1.get("lagna", {}), c2.get("lagna", {})

    asc1 = RASHI_NAMES.get(l1.get("Lg", {}).get("rashi"), "?")
    asc2 = RASHI_NAMES.get(l2.get("Lg", {}).get("rashi"), "?")
    header = f"Synastry: {name1} × {name2}  |  Asc1: {asc1}  |  Asc2: {asc2}"

    header_row = _syn_row("Planet", f"Zod({name1})", f"Zod({name2})",
                          f"Nak({name1})", f"Nak({name2})", "Aspect")
    separator = "-" * len(header_row)
    rows = [header, "```", header_row, separator]

    for key, full_name in PLANET_NAMES.items():
        p1, p2 = g1.get(key), g2.get(key)
        if not p1 or not p2:
            continue
        lng1, lng2 = p1.get("longitude"), p2.get("longitude")
        rows.append(_syn_row(
            full_name,
            RASHI_NAMES.get(p1.get("rashi"), "—"),
            RASHI_NAMES.get(p2.get("rashi"), "—"),
            (p1.get("nakshatra") or {}).get("name", "—"),
            (p2.get("nakshatra") or {}).get("name", "—"),
            get_aspect(lng1, lng2) if lng1 is not None and lng2 is not None else "—",
        ))

    rows.append("```")
    return "\n".join(rows)
