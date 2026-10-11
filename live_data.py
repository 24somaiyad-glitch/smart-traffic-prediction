"""Real-time data sources. Every function fails safely (returns None) so the app never crashes offline.
1) Clock          -> hour and day (no API needed)
2) Open-Meteo     -> live weather, FREE, no API key
3) TomTom Traffic -> live road speed, free tier, needs an API key (optional)"""
import os, datetime as dt
import requests
from zoneinfo import ZoneInfo

TZ = "Asia/Kolkata"                       # EDIT: your time zone
CITY_LAT, CITY_LON = 21.1458, 79.0882     # EDIT: your city centre
# EDIT: one sample point (lat, lon) on a main road of each area, used only for TomTom live speed
AREA_POINTS = {"Downtown": (21.1498, 79.0806), "Highway": (21.1700, 79.0500),
               "Residential": (21.1200, 79.1000), "Industrial": (21.0900, 79.0600)}

def now_local():
    return dt.datetime.now(ZoneInfo(TZ))

def weather_label(code, precip):
    if precip and precip > 0.1: return "Rain"
    if code in (45, 48): return "Fog"
    if code in range(51, 100): return "Rain"      # drizzle, rain, showers, thunderstorm (snow n/a)
    if code in (2, 3): return "Cloudy"
    return "Clear"

def get_live_weather(lat=CITY_LAT, lon=CITY_LON, timeout=5):
    """Returns {'weather': 'Rain', 'temp_c': 27.1} or None if offline."""
    try:
        r = requests.get("https://api.open-meteo.com/v1/forecast", timeout=timeout,
                         params={"latitude": lat, "longitude": lon, "current": "temperature_2m,weather_code,precipitation"})
        c = r.json()["current"]
        return {"weather": weather_label(c["weather_code"], c.get("precipitation", 0)), "temp_c": c["temperature_2m"]}
    except Exception:
        return None

def get_live_traffic_level(area, key=None, timeout=5):
    """Current congestion from TomTom Flow Segment Data. Returns (level, speed_ratio) or None.
    ratio = current speed / free-flow speed:  >0.75 Low | 0.5-0.75 Medium | <0.5 High"""
    key = key or os.getenv("TOMTOM_KEY")
    if not key or area not in AREA_POINTS: return None
    lat, lon = AREA_POINTS[area]
    try:
        r = requests.get("https://api.tomtom.com/traffic/services/4/flowSegmentData/absolute/10/json", timeout=timeout,
                         params={"key": key, "point": f"{lat},{lon}"})
        f = r.json()["flowSegmentData"]; ratio = f["currentSpeed"] / f["freeFlowSpeed"]
        return ("Low" if ratio > .75 else "Medium" if ratio > .5 else "High"), round(ratio, 2)
    except Exception:
        return None
