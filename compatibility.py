from constants import RASHI_NAMES, PLANET_NAMES, ZODIAC_LORDS

# ---------------------------------------------------------------------------
# Ashtakuta data tables
# ---------------------------------------------------------------------------

# Nadi: cycle of 3 for nakshatras 1-27
NADI = {n: ["Aadi", "Madhya", "Antya"][(n - 1) % 3] for n in range(1, 28)}

# Gana
GANA = {
    1: "Deva", 5: "Deva", 7: "Deva", 8: "Deva", 13: "Deva", 15: "Deva", 17: "Deva", 22: "Deva", 23: "Deva", 27: "Deva",
    2: "Manushya", 4: "Manushya", 11: "Manushya", 12: "Manushya", 20: "Manushya", 21: "Manushya", 25: "Manushya", 26: "Manushya",
    3: "Rakshasa", 6: "Rakshasa", 9: "Rakshasa", 10: "Rakshasa", 14: "Rakshasa", 16: "Rakshasa", 18: "Rakshasa", 19: "Rakshasa", 24: "Rakshasa",
}

# Yoni (animal, gender)
YONI = {
    1: ("Horse", "M"), 2: ("Elephant", "F"), 3: ("Goat", "F"), 4: ("Snake", "M"), 5: ("Snake", "F"),
    6: ("Dog", "F"), 7: ("Cat", "F"), 8: ("Goat", "M"), 9: ("Cat", "M"), 10: ("Rat", "M"),
    11: ("Rat", "F"), 12: ("Cow", "M"), 13: ("Buffalo", "F"), 14: ("Tiger", "F"), 15: ("Buffalo", "M"),
    16: ("Tiger", "M"), 17: ("Deer", "F"), 18: ("Deer", "M"), 19: ("Dog", "M"), 20: ("Monkey", "F"),
    21: ("Mongoose", "M"), 22: ("Monkey", "M"), 23: ("Lion", "F"), 24: ("Horse", "F"),
    25: ("Lion", "M"), 26: ("Cow", "F"), 27: ("Elephant", "M"),
}
YONI_ENEMIES = frozenset({
    ("Cow", "Tiger"), ("Tiger", "Cow"), ("Elephant", "Lion"), ("Lion", "Elephant"),
    ("Rat", "Cat"), ("Cat", "Rat"), ("Dog", "Deer"), ("Deer", "Dog"),
    ("Monkey", "Goat"), ("Goat", "Monkey"), ("Horse", "Buffalo"), ("Buffalo", "Horse"),
    ("Mongoose", "Snake"), ("Snake", "Mongoose"),
})

# Varna (by rashi number)
VARNA_RANK = {4: 3, 8: 3, 12: 3, 1: 2, 5: 2, 9: 2, 2: 1, 6: 1, 10: 1, 3: 0, 7: 0, 11: 0}
VARNA_NAMES = {3: "Brahmin", 2: "Kshatriya", 1: "Vaishya", 0: "Shudra"}

# Vashya
VASHYA = {
    1: "Chatushpada", 2: "Chatushpada", 5: "Chatushpada", 9: "Chatushpada", 10: "Chatushpada",
    3: "Dwipada", 6: "Dwipada", 7: "Dwipada", 11: "Dwipada",
    4: "Keeta", 8: "Keeta", 12: "Keeta",
}

# Planet friendship table for Graha Maitri
# Values: 1=friend, 0=neutral, -1=enemy
_PLANET_FRIENDS = {
    "Su": {"Mo": 1, "Ma": 1, "Ju": 1, "Me": 0, "Ve": -1, "Sa": -1},
    "Mo": {"Su": 1, "Me": 1, "Ma": 0, "Ju": 0, "Ve": 0, "Sa": 0},
    "Ma": {"Su": 1, "Mo": 1, "Ju": 1, "Ve": 0, "Sa": 0, "Me": -1},
    "Me": {"Su": 0, "Ve": 1, "Ra": 1, "Mo": -1, "Ma": 0, "Ju": 0, "Sa": 0},
    "Ju": {"Su": 1, "Mo": 1, "Ma": 1, "Sa": 0, "Me": -1, "Ve": -1},
    "Ve": {"Me": 1, "Sa": 1, "Mo": 0, "Ma": 0, "Ju": -1, "Su": -1},
    "Sa": {"Me": 1, "Ve": 1, "Mo": -1, "Su": -1, "Ma": -1, "Ju": 0},
}

# Map rashi → sign lord key
_RASHI_LORD_KEY = {
    1: "Ma", 2: "Ve", 3: "Me", 4: "Mo", 5: "Su", 6: "Me",
    7: "Ve", 8: "Ma", 9: "Ju", 10: "Sa", 11: "Sa", 12: "Ju",
}


def _get_friendship(lord1_key, lord2_key):
    """Return friendship value of lord1 toward lord2. 1=friend, 0=neutral, -1=enemy."""
    if lord1_key == lord2_key:
        return 1
    return _PLANET_FRIENDS.get(lord1_key, {}).get(lord2_key, 0)


def _graha_maitri_score(rashi1, rashi2):
    """
    Graha Maitri score (0-5) based on sign lords friendship.
    mutual friends=5, one friend=4, both neutral=3,
    one neutral one enemy=0.5, one friend one enemy=1, mutual enemies=0
    """
    lord1 = _RASHI_LORD_KEY.get(rashi1)
    lord2 = _RASHI_LORD_KEY.get(rashi2)
    if not lord1 or not lord2:
        return 0

    f12 = _get_friendship(lord1, lord2)
    f21 = _get_friendship(lord2, lord1)

    # mutual friends
    if f12 == 1 and f21 == 1:
        return 5
    # one friend, one neutral
    if (f12 == 1 and f21 == 0) or (f12 == 0 and f21 == 1):
        return 4
    # both neutral
    if f12 == 0 and f21 == 0:
        return 3
    # one friend, one enemy
    if (f12 == 1 and f21 == -1) or (f12 == -1 and f21 == 1):
        return 1
    # one neutral, one enemy
    if (f12 == 0 and f21 == -1) or (f12 == -1 and f21 == 0):
        return 0.5
    # mutual enemies
    if f12 == -1 and f21 == -1:
        return 0
    return 0


def compute_ashtakuta(data1, data2):
    """
    Compute all 8 Ashtakuta kutas.
    Uses Moon's rashi and nakshatra key.
    Returns list of (kuta_name, max_score, score, detail_str) or None if data missing.
    """
    def get_moon(data):
        moon = data.get("chart", {}).get("graha", {}).get("Mo", {})
        rashi = moon.get("rashi")
        nak_key = (moon.get("nakshatra") or {}).get("key")
        return rashi, nak_key

    rashi1, nak1 = get_moon(data1)
    rashi2, nak2 = get_moon(data2)

    if None in (rashi1, nak1, rashi2, nak2):
        return None

    results = []

    # 1. Varna (max 1)
    vr1 = VARNA_RANK.get(rashi1, 0)
    vr2 = VARNA_RANK.get(rashi2, 0)
    varna_score = 1 if vr2 >= vr1 else 0
    results.append(("Varna", 1, varna_score,
        f"{VARNA_NAMES.get(vr1,'?')} × {VARNA_NAMES.get(vr2,'?')}"))

    # 2. Vashya (max 2)
    v1 = VASHYA.get(rashi1, "Other")
    v2 = VASHYA.get(rashi2, "Other")
    if v1 == v2:
        vashya_score = 2
    elif v1 in ("Chatushpada", "Dwipada") and v2 in ("Chatushpada", "Dwipada"):
        vashya_score = 1
    else:
        vashya_score = 0
    results.append(("Vashya", 2, vashya_score, f"{v1} × {v2}"))

    # 3. Tara (max 3)
    # count nak1→nak2 and nak2→nak1, bad if mod 9 == 3,5,7
    BAD_TARAS = {3, 5, 7}
    count_12 = (nak2 - nak1) % 9
    count_21 = (nak1 - nak2) % 9
    # Adjust: if remainder is 0 treat as 9
    if count_12 == 0:
        count_12 = 9
    if count_21 == 0:
        count_21 = 9
    tara_12 = 0 if count_12 in BAD_TARAS else 1.5
    tara_21 = 0 if count_21 in BAD_TARAS else 1.5
    tara_score = tara_12 + tara_21
    results.append(("Tara", 3, tara_score,
        f"Nak {nak1}→{nak2}: pos {count_12}, {nak2}→{nak1}: pos {count_21}"))

    # 4. Yoni (max 4)
    y1 = YONI.get(nak1, ("?", "?"))
    y2 = YONI.get(nak2, ("?", "?"))
    animal1, gender1 = y1
    animal2, gender2 = y2
    if animal1 == animal2 and gender1 != gender2:
        yoni_score = 4
    elif (animal1, animal2) in YONI_ENEMIES or (animal2, animal1) in YONI_ENEMIES:
        yoni_score = 0
    elif animal1 == animal2 and gender1 == gender2:
        yoni_score = 2
    else:
        yoni_score = 3
    results.append(("Yoni", 4, yoni_score, f"{animal1}({gender1}) × {animal2}({gender2})"))

    # 5. Graha Maitri (max 5)
    gm_score = _graha_maitri_score(rashi1, rashi2)
    lord1_name = ZODIAC_LORDS.get(rashi1, "?")
    lord2_name = ZODIAC_LORDS.get(rashi2, "?")
    results.append(("Graha Maitri", 5, gm_score, f"{lord1_name} × {lord2_name}"))

    # 6. Gana (max 6)
    g1 = GANA.get(nak1, "?")
    g2 = GANA.get(nak2, "?")
    if g1 == g2:
        gana_score = 6
    elif (g1 == "Deva" and g2 == "Manushya") or (g1 == "Manushya" and g2 == "Deva"):
        gana_score = 5
    elif (g1 == "Deva" and g2 == "Rakshasa") or (g1 == "Rakshasa" and g2 == "Deva"):
        gana_score = 1
    else:  # Manushya + Rakshasa
        gana_score = 0
    results.append(("Gana", 6, gana_score, f"{g1} × {g2}"))

    # 7. Bhakoot (max 7)
    BAD_BHAKOOT = {(2, 12), (12, 2), (5, 9), (9, 5), (6, 8), (8, 6)}
    count_r12 = (rashi2 - rashi1) % 12 or 12
    count_r21 = (rashi1 - rashi2) % 12 or 12
    if (count_r12, count_r21) in BAD_BHAKOOT or (count_r21, count_r12) in BAD_BHAKOOT:
        bhakoot_score = 0
    else:
        bhakoot_score = 7
    results.append(("Bhakoot", 7, bhakoot_score,
        f"{RASHI_NAMES.get(rashi1,'?')} × {RASHI_NAMES.get(rashi2,'?')} ({count_r12}/{count_r21})"))

    # 8. Nadi (max 8)
    n1 = NADI.get(nak1, "?")
    n2 = NADI.get(nak2, "?")
    nadi_score = 8 if n1 != n2 else 0
    results.append(("Nadi", 8, nadi_score, f"{n1} × {n2}"))

    return results


def format_compatibility(data1, data2, name1, name2):
    """Format Ashtakuta compatibility report with bar chart and verdict."""
    kutas = compute_ashtakuta(data1, data2)
    if kutas is None:
        return "Could not determine Moon's nakshatra for one or both charts. Ensure chart data is complete."

    total = sum(score for _, _, score, _ in kutas)
    max_total = 36

    BAR_LEN = 8

    def bar(score, max_score):
        filled = round((score / max_score) * BAR_LEN) if max_score else 0
        return "█" * filled + "░" * (BAR_LEN - filled)

    pct = (total / max_total) * 100
    if pct >= 75:
        verdict = "Excellent"
    elif pct >= 60:
        verdict = "Good"
    elif pct >= 50:
        verdict = "Average"
    elif pct >= 36:
        verdict = "Below average"
    else:
        verdict = "Not recommended"

    W_name = 14
    W_bar = BAR_LEN
    W_score = 6

    def row(name, bar_str, score_str, detail):
        return f"  {name:<{W_name}} {bar_str}  {score_str}  {detail}"

    header = row("Kuta", "Bar     ", "Score ", "Detail")
    separator = "-" * len(header)

    lines = [
        f"**Ashtakuta Compatibility**",
        f"**{name1}** × **{name2}**",
        "```",
        header,
        separator,
    ]

    for kuta_name, max_score, score, detail in kutas:
        score_str = f"{score}/{max_score}"
        lines.append(row(kuta_name, bar(score, max_score), score_str, detail))

    lines += [
        separator,
        f"  {'Total':<{W_name}} {bar(total, max_total)}  {total}/{max_total}  {pct:.0f}%",
        "",
        f"  Verdict: {verdict}",
        "```",
    ]

    return "\n".join(lines)
