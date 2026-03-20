import os
import sys
import json
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Configuration
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
API_BASE_URL = os.getenv("JYOTISH_API_URL")
CHARTS_FILE = os.path.join(os.path.dirname(__file__), "saved_charts.json")

# Constants
RASHI_NAMES = {
    1: "Aries", 2: "Taurus", 3: "Gemini", 4: "Cancer",
    5: "Leo", 6: "Virgo", 7: "Libra", 8: "Scorpio",
    9: "Sagittarius", 10: "Capricorn", 11: "Aquarius", 12: "Pisces",
}

PLANET_NAMES = {
    "Su": "Sun", "Mo": "Moon", "Ma": "Mars", "Me": "Mercury",
    "Ju": "Jupiter", "Ve": "Venus", "Sa": "Saturn", "Ra": "Rahu", "Ke": "Ketu",
}

# Set up bot with required intents
intents = discord.Intents.default()
intents.message_content = True  # Required to read message content
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# File operations
def load_charts():
    if os.path.exists(CHARTS_FILE):
        with open(CHARTS_FILE, "r") as f:
            return json.load(f)
    return {}

def save_charts(charts):
    with open(CHARTS_FILE, "w") as f:
        json.dump(charts, f, indent=2)

def parse_datetime(date_str, time_str):
    """Parse ddmmyyyy and HHMMSS into components."""
    if len(date_str) != 8:
        raise ValueError(f"Date must be ddmmyyyy, got: {date_str!r}")
    if len(time_str) != 6:
        raise ValueError(f"Time must be HHMMSS, got: {time_str!r}")

    day = int(date_str[0:2])
    month = int(date_str[2:4])
    year = int(date_str[4:8])
    hour = int(time_str[0:2])
    minute = int(time_str[2:4])
    sec = int(time_str[4:6])

    return year, month, day, hour, minute, sec

def fetch_chart(date_str, time_str, latitude, longitude):
    """Call the Jyotish API and return parsed chart data."""
    year, month, day, hour, minute, sec = parse_datetime(date_str, time_str)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "year": year,
        "month": month,
        "day": day,
        "hour": hour,
        "min": minute,
        "sec": sec,
        "time_zone": "+00:00",
        "dst_hour": 0,
        "dst_min": 0,
        "nesting": 0,
        "varga": "D1",
        "infolevel": "basic",
    }

    resp = requests.get(f"{API_BASE_URL}/api/calculate", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()

def determine_bhava(planet_longitude, bhava_data):
    """Determine which bhava (house) a planet occupies."""
    bhava_cusps = []
    for i in range(1, 13):
        bh = bhava_data.get(str(i), {})
        lng = bh.get("longitude")
        if lng is not None:
            bhava_cusps.append((i, lng % 360))

    if not bhava_cusps:
        return None

    # Sort by longitude
    bhava_cusps.sort(key=lambda x: x[1])
    planet_lng = planet_longitude % 360

    # Find the house whose cusp is <= planet longitude
    bhava = bhava_cusps[0][0]
    for house_num, cusp_lng in bhava_cusps:
        if planet_lng >= cusp_lng:
            bhava = house_num
        else:
            break

    return bhava

def format_chart(chart_data):
    """Format the chart response into Discord message lines."""
    chart = chart_data.get("chart", {})
    graha = chart.get("graha", {})
    bhava = chart.get("bhava", {})

    lines = []
    for key, full_name in PLANET_NAMES.items():
        planet = graha.get(key)
        if not planet:
            continue

        rashi_num = planet.get("rashi")
        zodiac = RASHI_NAMES.get(rashi_num, f"Rashi {rashi_num}")

        nakshatra_info = planet.get("nakshatra", {})
        nakshatra_name = nakshatra_info.get("name", "Unknown") if nakshatra_info else "Unknown"

        planet_lng = planet.get("longitude")
        house = determine_bhava(planet_lng, bhava) if planet_lng is not None else None
        house_str = str(house) if house else "?"

        lines.append(
            f"**{full_name}** in {house_str}th House **{zodiac}** ({nakshatra_name} Nakshatra)"
        )

    return "\n".join(lines) if lines else "No planetary data found."

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    print(f"Bot is in {len(bot.guilds)} guilds")

@bot.command(name='chart', aliases=['c'])
async def chart_command(ctx, *args):
    """
    Show planetary positions for a given birth time or retrieve a saved chart.
    
    Usage:
      !chart ddmmyyyy HHMMSS Latitude Longitude
      !chart <saved_name>
    """
    charts = load_charts()
    
    # Single word arg - look up saved chart
    if len(args) == 1:
        name = args[0]
        if name in charts:
            saved = charts[name]
            formatted = format_chart(saved["data"])
            await ctx.send(f"**{name}**'s Chart:\n{formatted}")
        else:
            await ctx.send(f"No saved chart named `{name}`. Use `!save {name} ddmmyyyy HHMMSS Lat Lon` to save one.")
        return
    
    # Full chart calculation
    if len(args) != 4:
        await ctx.send(
            "**Usage:**\n"
            "`!chart ddmmyyyy HHMMSS Latitude Longitude` - Calculate a new chart\n"
            "`!chart <saved_name>` - Retrieve a saved chart"
        )
        return
    
    date_str, time_str, lat_str, lon_str = args
    
    # Validate coordinates
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except ValueError:
        await ctx.send("❌ Latitude and Longitude must be numbers.")
        return
    
    # Show typing indicator while fetching
    async with ctx.typing():
        try:
            data = fetch_chart(date_str, time_str, lat, lon)
        except ValueError as e:
            await ctx.send(f"❌ Input error: {e}")
            return
        except requests.HTTPError as e:
            await ctx.send(f"❌ API error: {e}")
            return
        except Exception as e:
            await ctx.send(f"❌ Error fetching chart: {e}")
            return
        
        formatted = format_chart(data)
    
    await ctx.send(f"**Chart for {date_str} {time_str}** at {lat}, {lon}:\n{formatted}")

@bot.command(name='save')
async def save_command(ctx, name, date_str, time_str, lat_str, lon_str):
    """
    Save a chart with a name for later retrieval.
    
    Usage: !save <name> ddmmyyyy HHMMSS Latitude Longitude
    """
    # Validate coordinates
    try:
        lat = float(lat_str)
        lon = float(lon_str)
    except ValueError:
        await ctx.send("❌ Latitude and Longitude must be numbers.")
        return
    
    # Show typing indicator while fetching
    async with ctx.typing():
        try:
            data = fetch_chart(date_str, time_str, lat, lon)
        except ValueError as e:
            await ctx.send(f"❌ Input error: {e}")
            return
        except requests.HTTPError as e:
            await ctx.send(f"❌ API error: {e}")
            return
        except Exception as e:
            await ctx.send(f"❌ Error fetching chart: {e}")
            return
        
        # Save the chart
        charts = load_charts()
        charts[name] = {
            "date": date_str,
            "time": time_str,
            "latitude": lat,
            "longitude": lon,
            "data": data,
        }
        save_charts(charts)
    
    await ctx.send(f"✅ Chart saved as `{name}`")

@bot.command(name='list', aliases=['saved'])
async def list_command(ctx):
    """List all saved charts."""
    charts = load_charts()
    
    if not charts:
        await ctx.send("No saved charts yet. Use `!save` to create one.")
        return
    
    lines = ["**Saved charts:**"]
    for name, data in charts.items():
        lines.append(f"• `{name}`: {data['date']} {data['time']} at {data['latitude']}, {data['longitude']}")
    
    await ctx.send("\n".join(lines))

@bot.command(name='delete')
async def delete_command(ctx, name):
    """Delete a saved chart."""
    charts = load_charts()
    
    if name not in charts:
        await ctx.send(f"No saved chart named `{name}`")
        return
    
    del charts[name]
    save_charts(charts)
    await ctx.send(f"✅ Deleted chart `{name}`")

@bot.command(name='help')
async def help_command(ctx):
    """Show help message."""
    help_text = """
**AstroBot Commands**

**Chart Calculation:**
`!chart ddmmyyyy HHMMSS Latitude Longitude`
Example: `!chart 15031990 143000 28.6139 77.2090`

**Saved Charts:**
`!chart <name>` - Show a saved chart
`!save <name> ddmmyyyy HHMMSS Latitude Longitude` - Save a chart
`!list` - List all saved charts
`!delete <name>` - Delete a saved chart

**Notes:**
• Date format: DDMMYYYY
• Time format: 24-hour HHMMSS
• Coordinates: Decimal degrees
"""
    await ctx.send(help_text)

@bot.event
async def on_command_error(ctx, error):
    """Handle command errors gracefully."""
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument: {error.param.name}\nUse `!help` for usage.")
    elif isinstance(error, commands.CommandNotFound):
        pass  # Ignore unknown commands
    else:
        await ctx.send(f"❌ An error occurred: {str(error)}")
        # Log the full error for debugging
        print(f"Error in {ctx.command}: {error}")

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable is not set.")
        sys.exit(1)
    
    print("Starting AstroBot...")
    bot.run(DISCORD_TOKEN)