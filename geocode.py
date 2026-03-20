import os
import json
import google.generativeai as genai

def resolve_location(place: str, date_str: str) -> dict:
    """
    Use Gemini to resolve a place name to lat/lon and UTC timezone offset.

    Args:
        place: City and country, e.g. "New Delhi, India"
        date_str: Date in ddmmyyyy format (used to determine correct DST offset)

    Returns:
        dict with keys: latitude (float), longitude (float), timezone (str, e.g. "+05:30")
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY environment variable is not set.")

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(os.getenv("MODEL"))

    day = date_str[0:2]
    month = date_str[2:4]
    year = date_str[4:8]

    prompt = (
        f'For the place "{place}" on {year}-{month}-{day}:\n'
        "1. What is the latitude and longitude?\n"
        "2. What is the UTC offset for that place on that specific date "
        "(accounting for Daylight Saving Time if applicable)?\n\n"
        "Respond ONLY with a JSON object — no markdown, no explanation:\n"
        '{"latitude": <float>, "longitude": <float>, "timezone": "<+HH:MM or -HH:MM>"}'
    )

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Strip markdown code fences if Gemini wraps in ```json ... ```
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.strip()

    result = json.loads(raw)

    # Validate timezone format: must be +HH:MM or -HH:MM (zero-padded)
    tz = result.get("timezone", "+00:00")
    sign = tz[0] if tz[0] in ("+", "-") else "+"
    parts = tz.lstrip("+-").split(":")
    h = parts[0].zfill(2)
    m = parts[1].zfill(2) if len(parts) > 1 else "00"
    result["timezone"] = f"{sign}{h}:{m}"

    return result
