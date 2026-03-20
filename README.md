# AstroBot — Vedic Astrology Discord Bot

A feature-rich Discord bot for Vedic (Jyotish) astrology. Generate birth charts, analyze planetary positions, calculate dashas, check compatibility, pull panchanga, and more — all from Discord.

## Features

### Charts
- `!chart` — Birth chart (Lagna/Ascendant based)
- `!sunchart` — Chart relative to Sun sign
- `!moonchart` — Chart relative to Moon sign
- `!prashna <City, Country>` — Prashna (horary) chart for the current moment
- `!varga <D9> <chart>` — All 16 divisional charts (D1, D2, D3, D4, D7, D9, D10, D12, D16, D20, D24, D27, D30, D40, D45, D60)

### Planets & Karakas
- `!sun` `!moon` `!mars` `!mercury` `!jupiter` `!venus` `!saturn` `!rahu` `!ketu` — Detailed planet analysis
- `!karaka <chart>` — Full Jaimini Sapta Karaka table
- `!atmakaraka` `!amatyakaraka` `!bhratrukaraka` `!matrukaraka` `!putrakaraka` `!gnatikaraka` `!darakaraka` — Individual karaka planet detail

### Dasha & Timing
- `!dasha <chart>` — Vimshottari dasha timeline with current Mahadasha, Antardasha, and Pratyantardasha

### Panchanga & Muhurta
- `!panchanga [City, Country]` — Tithi, Nakshatra, Yoga, Vara, Karana for now or a specific time
- `!muhurta <date> <time> <City, Country> [| activity]` — Muhurta assessment with Gemini AI

### Compatibility
- `!compat <chart1> <chart2>` — Ashtakuta compatibility with 8 kuta scores, bar chart, and verdict

### Other
- `!synastry <chart1> <chart2>` — Western-style synastry with planetary aspects
- `!transit <planet> <City, Country>` — Current transit position of any planet
- `!rising <planet> <City, Country>` — Rise, transit, and set times
- `!affirmation [City, Country]` — Daily Vedic affirmation based on current planetary positions
- `!tarot <question>` — 3-card tarot reading (truly random draw, Gemini AI interpretation)

### Saved Charts
- `!save <name> <date> <time> <City, Country>` — Save a birth chart
- `!list` — List your saved charts
- `!delete <name>` — Delete a saved chart
- `!rename <old> <new>` — Rename a saved chart

All commands accept either a **saved chart name** or an **inline chart** (`ddmmyyyy HHMMSS City, Country`).

## Tech Stack

- **Language** — Python 3
- **Discord** — discord.py
- **Astrology API** — [jyotish-api](https://github.com/teal33t/jyotish-api) by [@teal33t](https://github.com/teal33t)
- **AI** — Google Gemini API (geocoding, muhurta, affirmations, tarot)
- **Geocoding** — City/country → lat/lon/timezone via Gemini

## Setup

### Prerequisites
- Python 3.10+
- [jyotish-api](https://github.com/teal33t/jyotish-api) running locally or hosted (Docker)
- Discord bot token
- Google Gemini API key

### Installation

1. Clone the repo
   ```bash
   git clone https://github.com/yourusername/astrobot.git
   cd astrobot
   ```

2. Create and activate a virtual environment
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file
   ```
   DISCORD_TOKEN=your_discord_token
   JYOTISH_API_URL=http://localhost:9393
   GEMINI_API_KEY=your_gemini_api_key
   MODEL=gemini-2.0-flash-lite
   ```

5. Run the bot
   ```bash
   python bot.py
   ```

### Running jyotish-api

```bash
docker run -p 9393:9393 teal33t/jyotish-api
```

See [jyotish-api](https://github.com/teal33t/jyotish-api) for full setup instructions.

## Credits

Planetary calculations powered by [jyotish-api](https://github.com/teal33t/jyotish-api) by [@teal33t](https://github.com/teal33t) — a REST API for Vedic astrology built on Swiss Ephemeris.
