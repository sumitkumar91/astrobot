import os
import sys
import json
from datetime import date
import requests
import discord
from discord.ext import commands
from dotenv import load_dotenv

from geocode import resolve_location
from tarot import get_tarot_reading, format_tarot_reading
from api import fetch_chart, fetch_now, fetch_varga, fetch_dasha, fetch_panchanga
from charts import (
    format_chart, format_planet_detail,
    format_karakas, compute_karakas,
    format_synastry,
)
from varga import format_varga, VALID_VARGAS, VARGA_NAMES
from dasha import format_dasha
from panchanga import format_panchanga, assess_muhurta
from compatibility import format_compatibility
from affirmation import get_affirmation
from constants import (
    PLANET_NAMES, PLANET_COMMANDS, KARAKA_NAMES, KARAKA_COMMANDS,
    RASHI_NAMES, ZODIAC_LORDS, NAKSHATRA_LORDS,
)

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
CHARTS_FILE = os.path.join(os.path.dirname(__file__), "saved_charts.json")

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def load_charts():
    if os.path.exists(CHARTS_FILE):
        with open(CHARTS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_charts(charts):
    with open(CHARTS_FILE, "w") as f:
        json.dump(charts, f, indent=2)


def _display_name(key):
    """Strip user_id: prefix for display."""
    if ":" in key:
        return key.split(":", 1)[1]
    return key


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _is_date(token):
    t = token.strip(",")
    return len(t) == 8 and t.isdigit()


async def geocode_and_fetch(ctx, date_str, time_str, place):
    """Resolve place → lat/lon/tz via Gemini, then fetch chart. Returns (data, geo) or (None, None)."""
    try:
        geo = resolve_location(place, date_str)
    except Exception as e:
        await ctx.send(f"Could not resolve location `{place}`: {e}")
        return None, None
    try:
        data = fetch_chart(date_str, time_str, geo["latitude"], geo["longitude"], geo["timezone"])
    except ValueError as e:
        await ctx.send(f"Input error: {e}")
        return None, None
    except requests.HTTPError as e:
        await ctx.send(f"API error: {e}")
        return None, None
    except Exception as e:
        await ctx.send(f"Error fetching chart: {e}")
        return None, None
    return data, geo


async def resolve_chart_arg(ctx, tokens):
    """
    Resolve tokens to (chart_data, label) or (None, None).

    Formats:
      [saved_name]
      [ddmmyyyy] [HHMMSS] [City, Country...]

    For saved names, tries {ctx.author.id}:{name} first, then bare name (backward compat).
    """
    if not tokens:
        await ctx.send("No chart specified.")
        return None, None

    if _is_date(tokens[0]):
        if len(tokens) < 3:
            await ctx.send("Inline chart needs: `ddmmyyyy HHMMSS City, Country`")
            return None, None
        date_str = tokens[0].strip(",")
        time_str = tokens[1].strip(",")
        place = " ".join(tokens[2:]).strip(",")
        data, _ = await geocode_and_fetch(ctx, date_str, time_str, place)
        return data, f"{date_str} {time_str}, {place}"
    else:
        name = tokens[0]
        charts = load_charts()
        # Try user-scoped key first
        scoped_key = f"{ctx.author.id}:{name}"
        if scoped_key in charts:
            return charts[scoped_key]["data"], name
        # Fall back to bare name (backward compat)
        if name in charts:
            return charts[name]["data"], name
        await ctx.send(f"No saved chart named `{name}`. Use `!list` to see saved charts.")
        return None, None


async def resolve_refetch_params(ctx, tokens):
    """
    Returns (lat, lon, tz, date_str, time_str, label) or (None,None,None,None,None,None).
    For saved charts: uses stored lat/lon/timezone/date/time.
    For inline: geocodes and parses date/time from tokens.
    """
    if not tokens:
        await ctx.send("No chart specified.")
        return None, None, None, None, None, None

    if _is_date(tokens[0]):
        if len(tokens) < 3:
            await ctx.send("Inline chart needs: `ddmmyyyy HHMMSS City, Country`")
            return None, None, None, None, None, None
        date_str = tokens[0].strip(",")
        time_str = tokens[1].strip(",")
        place = " ".join(tokens[2:]).strip(",")
        try:
            geo = resolve_location(place, date_str)
        except Exception as e:
            await ctx.send(f"Could not resolve location `{place}`: {e}")
            return None, None, None, None, None, None
        label = f"{date_str} {time_str}, {place}"
        return geo["latitude"], geo["longitude"], geo["timezone"], date_str, time_str, label
    else:
        name = tokens[0]
        charts = load_charts()
        scoped_key = f"{ctx.author.id}:{name}"
        if scoped_key in charts:
            entry = charts[scoped_key]
        elif name in charts:
            entry = charts[name]
        else:
            await ctx.send(f"No saved chart named `{name}`. Use `!list` to see saved charts.")
            return None, None, None, None, None, None
        return (
            entry["latitude"], entry["longitude"], entry["timezone"],
            entry["date"], entry["time"], name
        )


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------

@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    print(f"Bot is in {len(bot.guilds)} guilds")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"Missing argument: {error.param.name}\nUse `!help` for usage.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"An error occurred: {str(error)}")
        print(f"Error in {ctx.command}: {error}")


# ---------------------------------------------------------------------------
# Chart commands
# ---------------------------------------------------------------------------

@bot.command(name='chart', aliases=['c'])
async def chart_command(ctx, *args):
    """!chart <saved_name>  or  !chart ddmmyyyy HHMMSS City, Country"""
    if not args:
        await ctx.send("`!chart ddmmyyyy HHMMSS City, Country`  or  `!chart <saved_name>`")
        return
    async with ctx.typing():
        data, label = await resolve_chart_arg(ctx, list(args))
        if data is None:
            return
        formatted = format_chart(data, reference="lagna")
    await ctx.send(f"**Chart — {label}**\n{formatted}")


@bot.command(name='sunchart')
async def sunchart_command(ctx, *args):
    """!sunchart <saved_name>  or  !sunchart ddmmyyyy HHMMSS City, Country"""
    if not args:
        await ctx.send("`!sunchart ddmmyyyy HHMMSS City, Country`  or  `!sunchart <saved_name>`")
        return
    async with ctx.typing():
        data, label = await resolve_chart_arg(ctx, list(args))
        if data is None:
            return
        formatted = format_chart(data, reference="sun")
    await ctx.send(f"**Sun Chart — {label}**\n{formatted}")


@bot.command(name='moonchart')
async def moonchart_command(ctx, *args):
    """!moonchart <saved_name>  or  !moonchart ddmmyyyy HHMMSS City, Country"""
    if not args:
        await ctx.send("`!moonchart ddmmyyyy HHMMSS City, Country`  or  `!moonchart <saved_name>`")
        return
    async with ctx.typing():
        data, label = await resolve_chart_arg(ctx, list(args))
        if data is None:
            return
        formatted = format_chart(data, reference="moon")
    await ctx.send(f"**Moon Chart — {label}**\n{formatted}")


@bot.command(name='prashna')
async def prashna_command(ctx, *args):
    """!prashna City, Country — chart for the current moment"""
    if not args:
        await ctx.send("`!prashna City, Country`  e.g. `!prashna Patna, India`")
        return
    place = " ".join(args).strip(",")
    async with ctx.typing():
        today = date.today().strftime("%d%m%Y")
        try:
            geo = resolve_location(place, today)
        except Exception as e:
            await ctx.send(f"Could not resolve location `{place}`: {e}")
            return
        try:
            data = fetch_now(geo["latitude"], geo["longitude"])
        except Exception as e:
            await ctx.send(f"Error fetching chart: {e}")
            return
        formatted = format_chart(data, reference="lagna")
    await ctx.send(f"**Prashna Chart — now, {place}**\n{formatted}")


# ---------------------------------------------------------------------------
# Tarot
# ---------------------------------------------------------------------------

@bot.command(name='tarot')
async def tarot_command(ctx, *args):
    """!tarot <your question>"""
    if not args:
        await ctx.send("`!tarot <your question>`  e.g. `!tarot what does my career hold?`")
        return
    question = " ".join(args)
    async with ctx.typing():
        try:
            reading = get_tarot_reading(question)
        except Exception as e:
            await ctx.send(f"Error getting tarot reading: {e}")
            return
        formatted = format_tarot_reading(reading)
    await ctx.send(formatted)


# ---------------------------------------------------------------------------
# Analysis commands
# ---------------------------------------------------------------------------

@bot.command(name='karaka')
async def karaka_command(ctx, *args):
    """!karaka <saved_name>  or  !karaka ddmmyyyy HHMMSS City, Country"""
    if not args:
        await ctx.send("`!karaka <saved_name>`  or  `!karaka ddmmyyyy HHMMSS City, Country`")
        return
    async with ctx.typing():
        data, label = await resolve_chart_arg(ctx, list(args))
        if data is None:
            return
        formatted = format_karakas(data, label)
    await ctx.send(formatted)


@bot.command(name='synastry')
async def synastry_command(ctx, *args):
    """
    !synastry <name1> <name2>
    !synastry <name1> ddmmyyyy HHMMSS City, Country
    !synastry ddmmyyyy HHMMSS Place | ddmmyyyy HHMMSS Place
    """
    if not args:
        await ctx.send(
            "`!synastry <name1> <name2>`\n"
            "`!synastry <name1> ddmmyyyy HHMMSS City, Country`\n"
            "`!synastry ddmmyyyy HHMMSS Place | ddmmyyyy HHMMSS Place`"
        )
        return

    tokens = list(args)

    if "|" in tokens:
        idx = tokens.index("|")
        spec1, spec2 = tokens[:idx], tokens[idx + 1:]
    elif _is_date(tokens[0]):
        await ctx.send("Use `|` to separate two inline charts.")
        return
    elif len(tokens) >= 2 and _is_date(tokens[1]):
        spec1, spec2 = [tokens[0]], tokens[1:]
    else:
        spec1 = [tokens[0]]
        spec2 = tokens[1:] if len(tokens) > 1 else []

    if not spec2:
        await ctx.send("Need two chart specs. Use `!help` for usage.")
        return

    async with ctx.typing():
        data1, label1 = await resolve_chart_arg(ctx, spec1)
        if data1 is None:
            return
        data2, label2 = await resolve_chart_arg(ctx, spec2)
        if data2 is None:
            return
        formatted = format_synastry(data1, data2, label1, label2)
    await ctx.send(formatted)


@bot.command(name='transit')
async def transit_command(ctx, planet_arg=None, *place_parts):
    """!transit <planet> City, Country"""
    if not planet_arg or not place_parts:
        await ctx.send(
            f"`!transit <planet> City, Country`\n"
            f"Planets: {', '.join(PLANET_COMMANDS.keys())}"
        )
        return

    p_key = PLANET_COMMANDS.get(planet_arg.lower().strip(","))
    if not p_key:
        await ctx.send(f"Unknown planet `{planet_arg}`. Choose from: {', '.join(PLANET_COMMANDS.keys())}")
        return

    place = " ".join(place_parts).strip(",")
    async with ctx.typing():
        today = date.today().strftime("%d%m%Y")
        try:
            geo = resolve_location(place, today)
        except Exception as e:
            await ctx.send(f"Could not resolve location `{place}`: {e}")
            return
        try:
            data = fetch_now(geo["latitude"], geo["longitude"])
        except Exception as e:
            await ctx.send(f"Error fetching transit data: {e}")
            return

        graha  = data.get("chart", {}).get("graha", {})
        planet = graha.get(p_key)
        if not planet:
            await ctx.send(f"No transit data found for {PLANET_NAMES[p_key]}.")
            return

        rashi_num = planet.get("rashi")
        zodiac    = RASHI_NAMES.get(rashi_num, "—")
        degree    = planet.get("degree", 0)
        longitude = planet.get("longitude", 0)
        speed     = planet.get("speed", 0)
        sign_lord = ZODIAC_LORDS.get(rashi_num, "—")
        nak_info  = planet.get("nakshatra") or {}
        nak_key   = nak_info.get("key")
        nak_lord  = NAKSHATRA_LORDS.get(nak_key, "—") if nak_key else "—"
        nak_left  = nak_info.get("left")

    await ctx.send(
        f"**{PLANET_NAMES[p_key]} Transit — {place}**\n"
        f"```"
        f"\nZodiac       {zodiac} ({sign_lord})"
        f"\nDegree       {degree:.4f}°  ({longitude:.4f}° abs)"
        f"\nNakshatra    {nak_info.get('name', '—')}, Pada {nak_info.get('pada', '—')}"
        f"\nNak Lord     {nak_lord}"
        f"\nDeg Left     {f'{nak_left:.2f}°' if nak_left is not None else '—'}"
        f"\nSpeed        {speed:+.4f}°/day  ({'retrograde' if speed < 0 else 'direct'})"
        f"\n```"
    )


# ---------------------------------------------------------------------------
# Divisional chart (Varga)
# ---------------------------------------------------------------------------

@bot.command(name='varga')
async def varga_command(ctx, *args):
    """!varga <D9> <chart_spec>  e.g. !varga D9 sumit  or  !varga D9 ddmmyyyy HHMMSS City, Country"""
    if len(args) < 2:
        await ctx.send(
            f"`!varga <varga> <saved_name>` or `!varga <varga> ddmmyyyy HHMMSS City, Country`\n"
            f"Valid vargas: {', '.join(VALID_VARGAS)}"
        )
        return

    varga_key = args[0].upper()
    if varga_key not in VALID_VARGAS:
        await ctx.send(f"Invalid varga `{varga_key}`. Valid: {', '.join(VALID_VARGAS)}")
        return

    tokens = list(args[1:])
    async with ctx.typing():
        lat, lon, tz, date_str, time_str, label = await resolve_refetch_params(ctx, tokens)
        if lat is None:
            return
        try:
            data = fetch_varga(date_str, time_str, lat, lon, tz, varga_key)
        except requests.HTTPError as e:
            await ctx.send(f"API error: {e}")
            return
        except Exception as e:
            await ctx.send(f"Error fetching varga: {e}")
            return
        formatted = format_varga(data, varga_key)
    await ctx.send(f"**{VARGA_NAMES.get(varga_key, varga_key)} — {label}**\n{formatted}")


# ---------------------------------------------------------------------------
# Dasha
# ---------------------------------------------------------------------------

@bot.command(name='dasha')
async def dasha_command(ctx, *args):
    """!dasha <saved_name>  or  !dasha ddmmyyyy HHMMSS City, Country"""
    if not args:
        await ctx.send("`!dasha <saved_name>`  or  `!dasha ddmmyyyy HHMMSS City, Country`")
        return
    tokens = list(args)
    async with ctx.typing():
        lat, lon, tz, date_str, time_str, label = await resolve_refetch_params(ctx, tokens)
        if lat is None:
            return
        try:
            data = fetch_dasha(date_str, time_str, lat, lon, tz)
        except requests.HTTPError as e:
            await ctx.send(f"API error: {e}")
            return
        except Exception as e:
            await ctx.send(f"Error fetching dasha: {e}")
            return
        formatted = format_dasha(data)
    await ctx.send(f"**Dasha — {label}**\n{formatted}")


# ---------------------------------------------------------------------------
# Panchanga
# ---------------------------------------------------------------------------

@bot.command(name='panchanga')
async def panchanga_command(ctx, *args):
    """
    !panchanga City, Country  — panchanga for now
    !panchanga ddmmyyyy HHMMSS City, Country  — panchanga for specific time
    """
    if not args:
        await ctx.send(
            "`!panchanga City, Country`\n"
            "`!panchanga ddmmyyyy HHMMSS City, Country`"
        )
        return

    tokens = list(args)
    async with ctx.typing():
        if _is_date(tokens[0]):
            if len(tokens) < 3:
                await ctx.send("Inline panchanga needs: `ddmmyyyy HHMMSS City, Country`")
                return
            date_str = tokens[0].strip(",")
            time_str = tokens[1].strip(",")
            place = " ".join(tokens[2:]).strip(",")
            try:
                geo = resolve_location(place, date_str)
            except Exception as e:
                await ctx.send(f"Could not resolve location `{place}`: {e}")
                return
            try:
                data = fetch_panchanga(date_str, time_str, geo["latitude"], geo["longitude"], geo["timezone"])
            except Exception as e:
                await ctx.send(f"Error fetching panchanga: {e}")
                return
            label = f"{date_str} {time_str}, {place}"
        else:
            place = " ".join(tokens).strip(",")
            today = date.today().strftime("%d%m%Y")
            try:
                geo = resolve_location(place, today)
            except Exception as e:
                await ctx.send(f"Could not resolve location `{place}`: {e}")
                return
            try:
                data = fetch_now(geo["latitude"], geo["longitude"])
            except Exception as e:
                await ctx.send(f"Error fetching panchanga: {e}")
                return
            label = f"now, {place}"

        formatted = format_panchanga(data)
    await ctx.send(f"**Panchanga — {label}**\n{formatted}")


# ---------------------------------------------------------------------------
# Muhurta
# ---------------------------------------------------------------------------

@bot.command(name='muhurta')
async def muhurta_command(ctx, *args):
    """
    !muhurta ddmmyyyy HHMMSS City, Country [| activity]
    """
    if not args:
        await ctx.send("`!muhurta ddmmyyyy HHMMSS City, Country [| activity]`")
        return

    tokens = list(args)

    # Split on | to extract optional activity
    activity = None
    if "|" in tokens:
        idx = tokens.index("|")
        activity = " ".join(tokens[idx + 1:]).strip()
        tokens = tokens[:idx]

    if not _is_date(tokens[0]) or len(tokens) < 3:
        await ctx.send("`!muhurta ddmmyyyy HHMMSS City, Country [| activity]`")
        return

    date_str = tokens[0].strip(",")
    time_str = tokens[1].strip(",")
    place = " ".join(tokens[2:]).strip(",")

    async with ctx.typing():
        try:
            geo = resolve_location(place, date_str)
        except Exception as e:
            await ctx.send(f"Could not resolve location `{place}`: {e}")
            return
        try:
            data = fetch_panchanga(date_str, time_str, geo["latitude"], geo["longitude"], geo["timezone"])
        except Exception as e:
            await ctx.send(f"Error fetching panchanga: {e}")
            return

        panchanga_text = format_panchanga(data)
        datetime_label = f"{date_str[:2]}/{date_str[2:4]}/{date_str[4:]} {time_str[:2]}:{time_str[2:4]}, {place}"
        try:
            assessment = assess_muhurta(data, activity, datetime_label)
        except Exception as e:
            await ctx.send(f"Error getting Gemini assessment: {e}")
            return

    title = f"**Muhurta — {datetime_label}**"
    if activity:
        title += f" for *{activity}*"
    await ctx.send(f"{title}\n{panchanga_text}\n\n**Assessment**\n{assessment}")


# ---------------------------------------------------------------------------
# Compatibility
# ---------------------------------------------------------------------------

@bot.command(name='compatibility', aliases=['compat'])
async def compatibility_command(ctx, *args):
    """
    !compatibility <chart1> <chart2>
    !compat <name1> <name2>
    !compat ddmmyyyy HHMMSS Place | ddmmyyyy HHMMSS Place
    """
    if not args:
        await ctx.send(
            "`!compat <name1> <name2>`\n"
            "`!compat <name1> ddmmyyyy HHMMSS City, Country`\n"
            "`!compat ddmmyyyy HHMMSS Place | ddmmyyyy HHMMSS Place`"
        )
        return

    tokens = list(args)

    if "|" in tokens:
        idx = tokens.index("|")
        spec1, spec2 = tokens[:idx], tokens[idx + 1:]
    elif _is_date(tokens[0]):
        await ctx.send("Use `|` to separate two inline charts.")
        return
    elif len(tokens) >= 2 and _is_date(tokens[1]):
        spec1, spec2 = [tokens[0]], tokens[1:]
    else:
        spec1 = [tokens[0]]
        spec2 = tokens[1:] if len(tokens) > 1 else []

    if not spec2:
        await ctx.send("Need two chart specs. Use `!help` for usage.")
        return

    async with ctx.typing():
        data1, label1 = await resolve_chart_arg(ctx, spec1)
        if data1 is None:
            return
        data2, label2 = await resolve_chart_arg(ctx, spec2)
        if data2 is None:
            return
        formatted = format_compatibility(data1, data2, label1, label2)
    await ctx.send(formatted)


# ---------------------------------------------------------------------------
# Rising / setting times
# ---------------------------------------------------------------------------

@bot.command(name='rising')
async def rising_command(ctx, planet_arg=None, *place_parts):
    """!rising <planet> City, Country"""
    if not planet_arg or not place_parts:
        await ctx.send(
            f"`!rising <planet> City, Country`\n"
            f"Planets: {', '.join(PLANET_COMMANDS.keys())}"
        )
        return

    p_key = PLANET_COMMANDS.get(planet_arg.lower().strip(","))
    if not p_key:
        await ctx.send(f"Unknown planet `{planet_arg}`. Choose from: {', '.join(PLANET_COMMANDS.keys())}")
        return

    place = " ".join(place_parts).strip(",")
    async with ctx.typing():
        today = date.today().strftime("%d%m%Y")
        try:
            geo = resolve_location(place, today)
        except Exception as e:
            await ctx.send(f"Could not resolve location `{place}`: {e}")
            return
        try:
            data = fetch_now(geo["latitude"], geo["longitude"])
        except Exception as e:
            await ctx.send(f"Error fetching data: {e}")
            return

        rising_data = data.get("chart", {}).get("rising", {})
        planet_rising = rising_data.get(p_key)
        if not planet_rising:
            await ctx.send(
                f"No rising/setting data available for **{PLANET_NAMES.get(p_key, p_key)}** "
                f"in {place}. The API may not provide this data for this planet."
            )
            return

        rise = planet_rising.get("rise", "—")
        set_ = planet_rising.get("set", "—")
        transit = planet_rising.get("transit", "—")

    await ctx.send(
        f"**{PLANET_NAMES.get(p_key, p_key)} Rising/Setting — {place}**\n"
        f"```"
        f"\nRise     {rise}"
        f"\nTransit  {transit}"
        f"\nSet      {set_}"
        f"\n```"
    )


# ---------------------------------------------------------------------------
# Daily Affirmation
# ---------------------------------------------------------------------------

@bot.command(name='affirmation')
async def affirmation_command(ctx, *args):
    """!affirmation [City, Country]"""
    async with ctx.typing():
        if args:
            place = " ".join(args).strip(",")
            today = date.today().strftime("%d%m%Y")
            try:
                geo = resolve_location(place, today)
            except Exception as e:
                await ctx.send(f"Could not resolve location `{place}`: {e}")
                return
            lat, lon = geo["latitude"], geo["longitude"]
        else:
            lat, lon = 35.7219, 51.3347  # default coords

        try:
            data = fetch_now(lat, lon)
        except Exception as e:
            await ctx.send(f"Error fetching current positions: {e}")
            return

        try:
            text = get_affirmation(data)
        except Exception as e:
            await ctx.send(f"Error generating affirmation: {e}")
            return

    await ctx.send(f"**Daily Affirmation**\n{text}")


# ---------------------------------------------------------------------------
# Saved chart management
# ---------------------------------------------------------------------------

@bot.command(name='save')
async def save_command(ctx, *args):
    """!save <name> ddmmyyyy HHMMSS City, Country"""
    if len(args) < 4:
        await ctx.send("`!save <name> ddmmyyyy HHMMSS City, Country`")
        return
    name, date_str, time_str, *place_parts = args
    place = " ".join(place_parts)
    async with ctx.typing():
        data, geo = await geocode_and_fetch(ctx, date_str, time_str, place)
        if data is None:
            return
        charts = load_charts()
        scoped_key = f"{ctx.author.id}:{name}"
        charts[scoped_key] = {
            "date": date_str, "time": time_str, "place": place,
            "latitude": geo["latitude"], "longitude": geo["longitude"],
            "timezone": geo["timezone"], "data": data,
        }
        save_charts(charts)
    await ctx.send(f"Chart saved as `{name}`")


@bot.command(name='list', aliases=['saved'])
async def list_command(ctx):
    """List your saved charts."""
    charts = load_charts()
    prefix = f"{ctx.author.id}:"
    user_charts = {k: v for k, v in charts.items() if k.startswith(prefix)}
    if not user_charts:
        await ctx.send("You have no saved charts. Use `!save` to create one.")
        return
    lines = ["**Your saved charts:**"]
    for key, data in user_charts.items():
        display = _display_name(key)
        place = data.get("place", f"{data.get('latitude')}, {data.get('longitude')}")
        lines.append(f"• `{display}`: {data['date']} {data['time']} in {place}")
    await ctx.send("\n".join(lines))


@bot.command(name='delete')
async def delete_command(ctx, name):
    """Delete one of your saved charts."""
    charts = load_charts()
    scoped_key = f"{ctx.author.id}:{name}"
    if scoped_key in charts:
        del charts[scoped_key]
        save_charts(charts)
        await ctx.send(f"Deleted chart `{name}`")
    elif name in charts:
        del charts[name]
        save_charts(charts)
        await ctx.send(f"Deleted chart `{name}`")
    else:
        await ctx.send(f"No saved chart named `{name}`")


@bot.command(name='rename')
async def rename_command(ctx, old_name=None, new_name=None):
    """!rename <old_name> <new_name>"""
    if not old_name or not new_name:
        await ctx.send("`!rename <old_name> <new_name>`")
        return
    charts = load_charts()
    old_key = f"{ctx.author.id}:{old_name}"
    new_key = f"{ctx.author.id}:{new_name}"

    if old_key not in charts:
        if old_name in charts:
            old_key = old_name
            new_key = f"{ctx.author.id}:{new_name}"
        else:
            await ctx.send(f"No saved chart named `{old_name}`")
            return

    if new_key in charts:
        await ctx.send(f"A chart named `{new_name}` already exists. Delete it first.")
        return

    charts[new_key] = charts.pop(old_key)
    save_charts(charts)
    await ctx.send(f"Renamed `{old_name}` → `{new_name}`")


@bot.command(name='help')
async def help_command(ctx):
    await ctx.send("""**AstroBot Commands**

All chart commands accept a **saved name** or inline **ddmmyyyy HHMMSS City, Country**.

**Charts**
`!chart` · `!sunchart` · `!moonchart` · `!prashna City, Country`

**Planet detail**
`!sun` `!moon` `!mars` `!mercury` `!jupiter` `!venus` `!saturn` `!rahu` `!ketu`

**Karaka detail**
`!atmakaraka` `!amatyakaraka` `!bhratrukaraka` `!matrukaraka`
`!putrakaraka` `!gnatikaraka` `!darakaraka`

**Divisional Charts**
`!varga <D9> <chart_spec>` — e.g. `!varga D9 sumit` or `!varga D9 ddmmyyyy HHMMSS City`
Valid: D1 D2 D3 D4 D7 D9 D10 D12 D16 D20 D24 D27 D30 D40 D45 D60

**Dasha**
`!dasha <chart_spec>` — Vimshottari dasha timeline

**Panchanga & Muhurta**
`!panchanga [ddmmyyyy HHMMSS] City, Country`
`!muhurta ddmmyyyy HHMMSS City, Country [| activity]`

**Compatibility**
`!compat <chart1> <chart2>` — Ashtakuta compatibility
`!compat ddmmyyyy HHMMSS Place | ddmmyyyy HHMMSS Place`

**Other**
`!karaka` — full karaka table
`!synastry <chart1> <chart2>`
`!transit <planet> City, Country`
`!rising <planet> City, Country`
`!affirmation [City, Country]`
`!tarot <question>`

**Saved charts**
`!save <name> ddmmyyyy HHMMSS City, Country`
`!list` · `!delete <name>` · `!rename <old> <new>`""")


# ---------------------------------------------------------------------------
# Dynamic planet + karaka commands
# ---------------------------------------------------------------------------

def _make_planet_cmd(p_key):
    p_name = PLANET_NAMES[p_key].lower()

    async def _cmd(ctx, *args):
        if not args:
            await ctx.send(f"`!{p_name} <saved_name>`  or  `!{p_name} ddmmyyyy HHMMSS City, Country`")
            return
        async with ctx.typing():
            data, label = await resolve_chart_arg(ctx, list(args))
            if data is None:
                return
            formatted = format_planet_detail(data, p_key, label)
        await ctx.send(formatted)

    _cmd.__name__ = p_name
    return _cmd


def _make_karaka_cmd(k_index):
    k_name = KARAKA_NAMES[k_index][0]

    async def _cmd(ctx, *args):
        if not args:
            await ctx.send(f"`!{k_name.lower()} <saved_name>`  or  `!{k_name.lower()} ddmmyyyy HHMMSS City, Country`")
            return
        async with ctx.typing():
            data, label = await resolve_chart_arg(ctx, list(args))
            if data is None:
                return
            karakas = compute_karakas(data)
            if k_index >= len(karakas):
                await ctx.send(f"Could not determine {k_name} from chart data.")
                return
            _, abbr, _, planet_name, _ = karakas[k_index]
            p_key = next(k for k, v in PLANET_NAMES.items() if v == planet_name)
            formatted = format_planet_detail(data, p_key, label, karaka_label=f"{k_name} · {abbr}")
        await ctx.send(formatted)

    _cmd.__name__ = k_name.lower()
    return _cmd


for _cmd_name, _p_key in PLANET_COMMANDS.items():
    bot.command(name=_cmd_name)(_make_planet_cmd(_p_key))

for _cmd_name, _k_index in KARAKA_COMMANDS.items():
    bot.command(name=_cmd_name)(_make_karaka_cmd(_k_index))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN environment variable is not set.")
        sys.exit(1)
    print("Starting AstroBot...")
    bot.run(DISCORD_TOKEN)
