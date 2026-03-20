import os
import json
import random
import google.generativeai as genai


# Full 78-card Rider-Waite deck
TAROT_DECK = [
    # Major Arcana (22)
    "The Fool", "The Magician", "The High Priestess", "The Empress", "The Emperor",
    "The Hierophant", "The Lovers", "The Chariot", "Strength", "The Hermit",
    "Wheel of Fortune", "Justice", "The Hanged Man", "Death", "Temperance",
    "The Devil", "The Tower", "The Star", "The Moon", "The Sun",
    "Judgement", "The World",
    # Minor Arcana — Wands (14)
    "Ace of Wands", "Two of Wands", "Three of Wands", "Four of Wands",
    "Five of Wands", "Six of Wands", "Seven of Wands", "Eight of Wands",
    "Nine of Wands", "Ten of Wands", "Page of Wands", "Knight of Wands",
    "Queen of Wands", "King of Wands",
    # Minor Arcana — Cups (14)
    "Ace of Cups", "Two of Cups", "Three of Cups", "Four of Cups",
    "Five of Cups", "Six of Cups", "Seven of Cups", "Eight of Cups",
    "Nine of Cups", "Ten of Cups", "Page of Cups", "Knight of Cups",
    "Queen of Cups", "King of Cups",
    # Minor Arcana — Swords (14)
    "Ace of Swords", "Two of Swords", "Three of Swords", "Four of Swords",
    "Five of Swords", "Six of Swords", "Seven of Swords", "Eight of Swords",
    "Nine of Swords", "Ten of Swords", "Page of Swords", "Knight of Swords",
    "Queen of Swords", "King of Swords",
    # Minor Arcana — Pentacles (14)
    "Ace of Pentacles", "Two of Pentacles", "Three of Pentacles", "Four of Pentacles",
    "Five of Pentacles", "Six of Pentacles", "Seven of Pentacles", "Eight of Pentacles",
    "Nine of Pentacles", "Ten of Pentacles", "Page of Pentacles", "Knight of Pentacles",
    "Queen of Pentacles", "King of Pentacles",
]

POSITIONS = ["Past", "Present", "Future"]


def _draw_cards():
    """Randomly draw 3 distinct cards, each randomly upright or reversed."""
    cards = random.sample(TAROT_DECK, 3)
    return [
        {"position": pos, "card": card, "reversed": random.choice([True, False])}
        for pos, card in zip(POSITIONS, cards)
    ]


def get_tarot_reading(question: str) -> dict:
    """
    Draw 3 cards randomly, then ask Gemini only for interpretation.

    Returns:
      {
        "question": str,
        "cards": [
          {"position": str, "card": str, "reversed": bool, "meaning": str},
          ...
        ],
        "summary": str
      }
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    drawn = _draw_cards()

    card_lines = "\n".join(
        f'- {c["position"]}: {c["card"]} ({"reversed" if c["reversed"] else "upright"})'
        for c in drawn
    )

    prompt = (
        f'You are an experienced tarot reader. The querent asks: "{question}"\n\n'
        f"The following cards have been drawn:\n{card_lines}\n\n"
        "Interpret each card in 2-3 sentences, directly relevant to the question and its position. "
        "Then write a 2-3 sentence overall summary tying all three together.\n\n"
        "Respond ONLY with a JSON object — no markdown, no extra text:\n"
        '{\n'
        '  "cards": [\n'
        '    {"position": "Past",    "meaning": "<text>"},\n'
        '    {"position": "Present", "meaning": "<text>"},\n'
        '    {"position": "Future",  "meaning": "<text>"}\n'
        '  ],\n'
        '  "summary": "<text>"\n'
        '}'
    )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(os.getenv("MODEL"))
    response = model.generate_content(prompt)
    raw = response.text.strip()

    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    interpretations = {c["position"]: c["meaning"] for c in json.loads(raw)["cards"]}
    summary = json.loads(raw).get("summary", "")

    # Merge drawn cards with Gemini's interpretations
    cards = [
        {**c, "meaning": interpretations.get(c["position"], "")}
        for c in drawn
    ]

    return {"question": question, "cards": cards, "summary": summary}


def format_tarot_reading(reading: dict) -> str:
    lines = [f'**Tarot Reading — "{reading["question"]}"**', ""]

    for c in reading.get("cards", []):
        orientation = " *(Reversed)*" if c.get("reversed") else ""
        lines.append(f"**{c['position']} — {c['card']}{orientation}**")
        lines.append(c["meaning"])
        lines.append("")

    if reading.get("summary"):
        lines.append("**Overall**")
        lines.append(reading["summary"])

    return "\n".join(lines)
