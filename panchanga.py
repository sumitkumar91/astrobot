import os
import google.generativeai as genai

TITHI_NAMES = {
    1: "Pratipada", 2: "Dwitiya", 3: "Tritiya", 4: "Chaturthi", 5: "Panchami",
    6: "Shashthi", 7: "Saptami", 8: "Ashtami", 9: "Navami", 10: "Dashami",
    11: "Ekadashi", 12: "Dwadashi", 13: "Trayodashi", 14: "Chaturdashi",
    15: "Purnima", 30: "Amavasya",
}
VARA_NAMES = {
    "Su": "Sunday (Ravivar)", "Mo": "Monday (Somavar)", "Ma": "Tuesday (Mangalvar)",
    "Me": "Wednesday (Budhvar)", "Ju": "Thursday (Guruvar)",
    "Ve": "Friday (Shukravar)", "Sa": "Saturday (Shanivar)",
}


def format_panchanga(chart_data):
    panchanga = chart_data.get("chart", {}).get("panchanga", {})
    if not panchanga:
        return "No panchanga data found."

    tithi = panchanga.get("tithi", {})
    nakshatra = panchanga.get("nakshatra", {})
    yoga = panchanga.get("yoga", {})
    vara = panchanga.get("vara", {})
    karana = panchanga.get("karana", {})

    W = 14

    def line(label, value):
        return f"  {label:<{W}} {value}"

    tithi_key = tithi.get("key")
    tithi_name = TITHI_NAMES.get(tithi_key, tithi.get("name", "?"))

    rows = ["Panchanga", "```",
        "── Five Elements ─────────────────────────",
        line("Tithi",     f"{tithi_name} ({tithi.get('paksha','').title()} Paksha)  [{tithi.get('left',0):.1f}% left]"),
        line("Nakshatra", f"{nakshatra.get('name','?')}, Pada {nakshatra.get('pada','?')}  [{nakshatra.get('left',0):.1f}% left]"),
        line("Yoga",      f"{yoga.get('name','?')}  [{yoga.get('left',0):.1f}% left]"),
        line("Vara",      VARA_NAMES.get(vara.get("key",""), vara.get("name","?"))),
        line("Karana",    f"{karana.get('name','?')}  [{karana.get('left',0):.1f}% left]"),
        "```",
    ]
    return "\n".join(rows)


def assess_muhurta(chart_data, activity, datetime_label):
    """Ask Gemini to assess the muhurta auspiciousness from panchanga data."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY not set.")

    p = chart_data.get("chart", {}).get("panchanga", {})
    tithi = p.get("tithi", {})
    nak = p.get("nakshatra", {})
    yoga = p.get("yoga", {})
    vara = p.get("vara", {})
    karana = p.get("karana", {})

    summary = (
        f"Tithi: {tithi.get('name')} ({tithi.get('paksha')} paksha)\n"
        f"Nakshatra: {nak.get('name')}, Pada {nak.get('pada')}\n"
        f"Yoga: {yoga.get('name')}\nVara: {vara.get('name')}\nKarana: {karana.get('name')}"
    )

    prompt = (
        f"You are a Vedic astrology expert in muhurta (electional astrology).\n"
        f"Assess auspiciousness for: **{activity or 'general activities'}**\n"
        f"Date/Time: {datetime_label}\n\nPanchanga:\n{summary}\n\n"
        f"In 4-5 sentences: Is this a good muhurta? What are the key auspicious and "
        f"inauspicious elements? Any specific recommendation or caution?"
    )

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(os.getenv("MODEL"))
    return model.generate_content(prompt).text.strip()
