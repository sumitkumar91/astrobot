import os
import google.generativeai as genai
from constants import PLANET_NAMES, RASHI_NAMES


def get_affirmation(current_chart_data):
    """
    Generate a daily affirmation from current planetary positions + panchanga.
    Uses Gemini. Returns a string.
    """
    chart = current_chart_data.get("chart", {})
    graha = chart.get("graha", {})
    panchanga = chart.get("panchanga", {})

    planet_lines = []
    for key in ["Su", "Mo", "Ma", "Me", "Ju", "Ve", "Sa"]:
        p = graha.get(key)
        if not p:
            continue
        rashi = RASHI_NAMES.get(p.get("rashi"), "?")
        nak = (p.get("nakshatra") or {}).get("name", "?")
        retro = " (R)" if (p.get("speed") or 0) < 0 else ""
        planet_lines.append(f"{PLANET_NAMES.get(key, key)} in {rashi} ({nak}){retro}")

    vara = panchanga.get("vara", {}).get("name", "today")
    tithi = panchanga.get("tithi", {}).get("name", "")

    prompt = (
        "You are a Vedic astrology guide. Write a warm, uplifting daily affirmation "
        "(3-4 sentences) based on today's cosmic energy. Be specific to the planets mentioned. "
        "Keep it positive, grounded, and practical.\n\n"
        f"Day: {vara}\nTithi: {tithi}\nPlanets:\n" + "\n".join(f"- {p}" for p in planet_lines)
    )

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set.")
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(os.getenv("MODEL"))
    return model.generate_content(prompt).text.strip()
