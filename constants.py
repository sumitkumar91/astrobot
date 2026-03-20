RASHI_NAMES = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
    5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces",
}

PLANET_NAMES = {
    "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury",
    "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn", "Ra": "Rahu", "Ke": "Ketu",
}

ZODIAC_LORDS = {
    1: "Mars", 2: "Venus", 3: "Mercury", 4: "Moon",
    5: "Sun", 6: "Mercury", 7: "Venus", 8: "Mars",
    9: "Jupiter", 10: "Saturn", 11: "Saturn", 12: "Jupiter",
}

NAKSHATRA_LORDS = {
    1: "Ketu",    2: "Venus",   3: "Sun",     4: "Moon",    5: "Mars",
    6: "Rahu",    7: "Jupiter", 8: "Saturn",  9: "Mercury",
    10: "Ketu",   11: "Venus",  12: "Sun",    13: "Moon",   14: "Mars",
    15: "Rahu",   16: "Jupiter",17: "Saturn", 18: "Mercury",
    19: "Ketu",   20: "Venus",  21: "Sun",    22: "Moon",   23: "Mars",
    24: "Rahu",   25: "Jupiter",26: "Saturn", 27: "Mercury",
}

RASHI_AVASTHA_LABELS = {
    "exalted":      "Exalted (Uccha)",
    "moolatrikona": "Moola Trikona",
    "own":          "Own Sign (Swa)",
    "friend":       "Friend's Sign (Mitra)",
    "neutral":      "Neutral Sign (Sama)",
    "enemy":        "Enemy's Sign (Shatru)",
    "debilitated":  "Debilitated (Neecha)",
}

BALADI_LABELS = {
    "bala":    "Bala (Infant — weak)",
    "kumara":  "Kumara (Youth — growing)",
    "yuva":    "Yuva (Adult — strongest)",
    "vriddha": "Vriddha (Old — fading)",
    "mrita":   "Mrita (Dead — inert)",
}

JAGRADI_LABELS = {
    "jagrat":   "Jagrat (Fully awake)",
    "swapna":   "Swapna (Dreaming)",
    "sushupti": "Sushupti (Deep sleep — inert)",
}

BHAVA_CHAR_LABELS = {
    "kendra":   "Kendra (Angular — powerful)",
    "trikona":  "Trikona (Trine — auspicious)",
    "upachaya": "Upachaya (Growth house)",
    "dusthana": "Dusthana (Difficult house)",
    "maraka":   "Maraka (Death-inflicting)",
    "mishra":   "Mishra (Mixed results)",
}

RELATION_LABELS = {
    -2: "Bitter Enemy",
    -1: "Enemy",
     0: "Neutral",
     1: "Friend",
     2: "Great Friend",
}

KARAKA_NAMES = [
    ("Atmakaraka",    "AK",  "Soul, self, main purpose of life"),
    ("Amatyakaraka",  "AmK", "Profession, career, financial status"),
    ("Bhratrukaraka", "BK",  "Siblings, gurus, mental inclination"),
    ("Matrukaraka",   "MK",  "Mother, education, property"),
    ("Putrakaraka",   "PK",  "Children, intelligence, creativity"),
    ("Gnatikaraka",   "GK",  "Enemies, disease, obstacles"),
    ("Darakaraka",    "DK",  "Spouse, marriage, partnership"),
]

# Only the 7 planets used in Sapta Karaka (Rahu and Ketu excluded)
KARAKA_PLANETS = ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]

# Map lowercase command name → planet key
PLANET_COMMANDS = {
    "sun": "Su", "moon": "Mo", "mars": "Ma", "mercury": "Me",
    "jupiter": "Ju", "venus": "Ve", "saturn": "Sa", "rahu": "Ra", "ketu": "Ke",
}

# Map command name → karaka index in KARAKA_NAMES
KARAKA_COMMANDS = {
    "atmakaraka": 0, "amatyakaraka": 1, "bhratrukaraka": 2,
    "matrukaraka": 3, "putrakaraka": 4, "gnatikaraka": 5, "darakaraka": 6,
}
