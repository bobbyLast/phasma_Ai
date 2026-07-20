"""Thin weather fact-check for Kalshi temperature markets (Open-Meteo, no API key)."""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

import requests

CITY_COORDS = {
    "NYC": {"lat": 40.7128, "lon": -74.0060, "aliases": ("nyc", "new york", "ny-")},
    "CHI": {"lat": 41.8781, "lon": -87.6298, "aliases": ("chi", "chicago")},
    "LA": {"lat": 34.0522, "lon": -118.2437, "aliases": (" los angeles", "lax", "la-")},
    "BOS": {"lat": 42.3601, "lon": -71.0589, "aliases": ("bos", "boston")},
    "MIA": {"lat": 25.7617, "lon": -80.1918, "aliases": ("mia", "miami")},
    "SEA": {"lat": 47.6062, "lon": -122.3321, "aliases": ("sea", "seattle")},
    "DFW": {"lat": 32.7767, "lon": -96.7970, "aliases": ("dfw", "dallas")},
    "PHX": {"lat": 33.4484, "lon": -112.0740, "aliases": ("phx", "phoenix")},
    "PHL": {"lat": 39.9526, "lon": -75.1652, "aliases": ("phl", "philadelphia")},
    "ATL": {"lat": 33.7490, "lon": -84.3880, "aliases": ("atl", "atlanta")},
}


def detect_city(title: str, ticker: str) -> Optional[str]:
    blob = f"{title} {ticker}".lower()
    for code, meta in CITY_COORDS.items():
        if code.lower() in blob.replace(" ", ""):
            return code
        for alias in meta["aliases"]:
            if alias.strip() in blob:
                return code
    # ticker patterns KXHIGHNY, KXTEMPCHI
    m = re.search(r"KX(?:HIGH|LOW|TEMP)?([A-Z]{2,3})", ticker.upper())
    if m:
        frag = m.group(1)
        for code in CITY_COORDS:
            if code.startswith(frag) or frag.startswith(code[:2]):
                return code
        if frag in ("NY", "NYC"):
            return "NYC"
    return None


def parse_temp_range(title: str) -> Optional[Dict[str, Any]]:
    t = title or ""
    tl = t.lower()
    m = re.search(r"(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*°?", t)
    if m:
        return {"min": float(m.group(1)), "max": float(m.group(2)), "type": "range"}
    m = re.search(r"(?:above|over|>)\s*(\d+(?:\.\d+)?)", tl)
    if m:
        return {"min": float(m.group(1)), "max": 200.0, "type": "above"}
    m = re.search(r"(?:below|under|<)\s*(\d+(?:\.\d+)?)", tl)
    if m:
        return {"min": -100.0, "max": float(m.group(1)), "type": "below"}
    return None


def parse_market_date(ticker: str, title: str = "") -> Optional[datetime]:
    # e.g. 25DEC11 or 26JAN05
    m = re.search(r"(\d{2})([A-Z]{3})(\d{2})", (ticker or "").upper())
    if m:
        yy, mon, dd = int(m.group(1)), m.group(2), int(m.group(3))
        months = {
            "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4, "MAY": 5, "JUN": 6,
            "JUL": 7, "AUG": 8, "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12,
        }
        month = months.get(mon)
        if month:
            year = 2000 + yy
            try:
                return datetime(year, month, dd, tzinfo=timezone.utc)
            except ValueError:
                return None
    return None


def fetch_daily_high(city: str, day: datetime) -> Optional[float]:
    coords = CITY_COORDS.get(city)
    if not coords:
        return None
    date_str = day.strftime("%Y-%m-%d")
    # Prefer archive for past days; forecast API for today/future
    now = datetime.now(timezone.utc)
    use_archive = day.date() < now.date()
    base = "https://archive-api.open-meteo.com/v1/archive" if use_archive else "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": coords["lat"],
        "longitude": coords["lon"],
        "daily": "temperature_2m_max",
        "temperature_unit": "fahrenheit",
        "timezone": "America/New_York",
        "start_date": date_str,
        "end_date": date_str,
    }
    try:
        resp = requests.get(base, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        temps = (data.get("daily") or {}).get("temperature_2m_max") or []
        if temps and temps[0] is not None:
            return float(temps[0])
    except Exception:
        return None
    return None


def forecast_snapshot(title: str, ticker: str) -> Dict[str, Any]:
    """Capture weather context at virtual-bet open time."""
    city = detect_city(title, ticker)
    temp_range = parse_temp_range(title)
    day = parse_market_date(ticker, title)
    predicted_high = None
    if city and day:
        predicted_high = fetch_daily_high(city, day)
    return {
        "city": city,
        "event_date": day.isoformat() if day else None,
        "temp_range": temp_range,
        "forecast_high_f": predicted_high,
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "title": title,
        "ticker": ticker,
    }


def evaluate_settlement(
    weather_forecast: Optional[Dict[str, Any]],
    *,
    side: str = "BUY_YES",
) -> Tuple[Optional[bool], Dict[str, Any]]:
    """
    Fact-check weather market: does actual high fall in the claimed range?
    Returns (yes_resolved_true, details). Win for BUY_YES if range hit; BUY_NO opposite.
    """
    details: Dict[str, Any] = {"weather_correct": None}
    if not isinstance(weather_forecast, dict):
        return None, details
    city = weather_forecast.get("city")
    temp_range = weather_forecast.get("temp_range")
    day_raw = weather_forecast.get("event_date")
    if not city or not temp_range or not day_raw:
        return None, details
    try:
        day = datetime.fromisoformat(str(day_raw).replace("Z", "+00:00"))
    except ValueError:
        return None, details
    # Only settle after the calendar day ends (buffer)
    if datetime.now(timezone.utc) < day + timedelta(hours=28):
        details["status"] = "pending"
        return None, details
    actual = fetch_daily_high(city, day)
    details["weather_actual_high_f"] = actual
    if actual is None:
        return None, details
    lo = float(temp_range.get("min", -100))
    hi = float(temp_range.get("max", 200))
    hit = lo <= actual <= hi
    details["range_hit"] = hit
    details["weather_correct"] = hit
    side_u = str(side or "BUY_YES").upper()
    if "NO" in side_u:
        win = not hit
    else:
        win = hit
    return win, details
