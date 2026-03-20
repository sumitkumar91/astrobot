import os
import requests


def _base_url():
    url = os.getenv("JYOTISH_API_URL")
    if not url:
        raise RuntimeError("JYOTISH_API_URL environment variable is not set.")
    return url


def parse_datetime(date_str, time_str):
    """Parse ddmmyyyy and HHMMSS into (year, month, day, hour, minute, sec)."""
    date_str = date_str.strip(",")
    time_str = time_str.strip(",")
    if len(date_str) != 8:
        raise ValueError(f"Date must be ddmmyyyy, got: {date_str!r}")
    if len(time_str) != 6:
        raise ValueError(f"Time must be HHMMSS, got: {time_str!r}")

    return (
        int(date_str[4:8]),  # year
        int(date_str[2:4]),  # month
        int(date_str[0:2]),  # day
        int(time_str[0:2]),  # hour
        int(time_str[2:4]),  # minute
        int(time_str[4:6]),  # sec
    )


def fetch_chart(date_str, time_str, latitude, longitude, timezone="+00:00"):
    """Call /api/calculate and return parsed chart data."""
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
        "time_zone": timezone,
        "dst_hour": 0,
        "dst_min": 0,
        "nesting": 0,
        "varga": "D1",
        "infolevel": "basic",
    }

    resp = requests.get(f"{_base_url()}/api/calculate", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_now(latitude, longitude):
    """Call /api/now and return chart data for the current moment."""
    params = {"latitude": latitude, "longitude": longitude}
    resp = requests.get(f"{_base_url()}/api/now", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_varga(date_str, time_str, latitude, longitude, timezone, varga_key):
    """Fetch chart with a specific varga. Same as fetch_chart but varga param."""
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
        "time_zone": timezone,
        "dst_hour": 0,
        "dst_min": 0,
        "nesting": 0,
        "varga": varga_key,
        "infolevel": "basic",
    }

    resp = requests.get(f"{_base_url()}/api/calculate", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_dasha(date_str, time_str, latitude, longitude, timezone):
    """Fetch chart with nesting=1 for antardasha data."""
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
        "time_zone": timezone,
        "dst_hour": 0,
        "dst_min": 0,
        "nesting": 1,
        "varga": "D1",
        "infolevel": "basic",
    }

    resp = requests.get(f"{_base_url()}/api/calculate", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_panchanga(date_str, time_str, latitude, longitude, timezone):
    """Fetch chart with infolevel=basic,panchanga."""
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
        "time_zone": timezone,
        "dst_hour": 0,
        "dst_min": 0,
        "nesting": 0,
        "varga": "D1",
        "infolevel": "basic,panchanga",
    }

    resp = requests.get(f"{_base_url()}/api/calculate", params=params, timeout=30)
    resp.raise_for_status()
    return resp.json()
