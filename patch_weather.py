#!/usr/bin/env python3
"""
Patch wxLocations for Morocco trip.
Run: python3 patch_weather.py
"""
import json, urllib.request

CHAT_ID  = "-5046151729"        # from /myid in your Telegram group
BASE_URL = "https://tripobot-production.up.railway.app"  # e.g. https://tripobot.up.railway.app

WX_LOCATIONS = [
    {
        "name": "Marrakech — Arrival",
        "tag": "4 Mar",
        "lat": 31.6295, "lon": -7.9811,
        "dateFrom": "2026-03-04", "dateTo": "2026-03-04",
        "wind": False, "snow": False,
        "forecastUrl": "https://www.accuweather.com/en/ma/marrakesh/244231/march-weather/244231",
        "forecastName": "AccuWeather — Marrakech March"
    },
    {
        "name": "Tinghir",
        "tag": "5 Mar night",
        "lat": 31.5151, "lon": -5.5253,
        "dateFrom": "2026-03-05", "dateTo": "2026-03-06",
        "wind": False, "snow": False,
        "forecastUrl": "https://www.accuweather.com/en/ma/tineghir/245870/march-weather/245870",
        "forecastName": "AccuWeather — Tinghir March"
    },
    {
        "name": "Merzouga — Sahara",
        "tag": "6–7 Mar",
        "lat": 31.0804, "lon": -3.9733,
        "dateFrom": "2026-03-06", "dateTo": "2026-03-07",
        "wind": False, "snow": False,
        "forecastUrl": "https://www.accuweather.com/en/ma/merzouga/244388/march-weather/244388",
        "forecastName": "AccuWeather — Merzouga March"
    },
    {
        "name": "Marrakech — Last Day",
        "tag": "8 Mar",
        "lat": 31.6295, "lon": -7.9811,
        "dateFrom": "2026-03-08", "dateTo": "2026-03-08",
        "wind": False, "snow": False,
        "forecastUrl": "https://www.accuweather.com/en/ma/marrakesh/244231/march-weather/244231",
        "forecastName": "AccuWeather — Marrakech March"
    },
]

def fetch(url):
    with urllib.request.urlopen(url) as r:
        return json.loads(r.read())

def post(url, payload):
    body = json.dumps(payload).encode()
    req  = urllib.request.Request(url, data=body,
                                  headers={"Content-Type": "application/json"},
                                  method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

# 1. Fetch existing data (preserves days, accoms, refs, etc.)
print("Fetching current data...")
data = fetch(f"{BASE_URL}/api/data?chat_id={CHAT_ID}")

# 2. Patch only wxLocations
data["wxLocations"] = WX_LOCATIONS

# 3. Save back
print("Saving...")
result = post(f"{BASE_URL}/api/data?chat_id={CHAT_ID}", data)
print("Done:", result)
print(f"\n{len(WX_LOCATIONS)} weather locations set:")
for loc in WX_LOCATIONS:
    print(f"  • {loc['name']} ({loc['dateFrom']} → {loc['dateTo']})")
