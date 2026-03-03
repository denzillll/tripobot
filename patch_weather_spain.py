#!/usr/bin/env python3
"""
Patch wxLocations for Spain trip (26 Feb – 1 Mar 2026).
Run: python3 patch_weather_spain.py
"""
import json, urllib.request

CHAT_ID  = "-1003724580501"
BASE_URL = "https://tripobot-production.up.railway.app"  # ← your Railway URL

WX_LOCATIONS = [
    {
        "name": "Burgos",
        "tag": "26 Feb",
        "lat": 42.3440, "lon": -3.6969,
        "dateFrom": "2026-02-26", "dateTo": "2026-02-26",
        "wind": False, "snow": False,
        "forecastUrl": "https://www.accuweather.com/en/es/burgos/307142/daily-weather-forecast/307142",
        "forecastName": "AccuWeather — Burgos"
    },
    {
        "name": "Arenas de Cabrales — Picos base",
        "tag": "27 Feb",
        "lat": 43.2556, "lon": -4.8456,
        "dateFrom": "2026-02-27", "dateTo": "2026-03-01",
        "wind": False, "snow": False,
        "forecastUrl": "https://www.accuweather.com/en/es/arenas/2323185/daily-weather-forecast/2323185",
        "forecastName": "AccuWeather — Arenas de Cabrales"
    },
    {
        "name": "Lagos de Covadonga",
        "tag": "27 Feb",
        "lat": 43.2697, "lon": -4.9967,
        "dateFrom": "2026-02-27", "dateTo": "2026-02-27",
        "wind": False, "snow": True,
        "forecastUrl": "https://www.accuweather.com/en/es/arenas/2323185/daily-weather-forecast/2323185",
        "forecastName": "AccuWeather — Arenas de Cabrales (Covadonga area)"
    },
    {
        "name": "Ruta del Cares — Poncebos",
        "tag": "28 Feb",
        "lat": 43.2339, "lon": -4.8622,
        "dateFrom": "2026-02-28", "dateTo": "2026-02-28",
        "wind": False, "snow": False,
        "forecastUrl": "https://www.accuweather.com/en/es/arenas/2323185/daily-weather-forecast/2323185",
        "forecastName": "AccuWeather — Arenas de Cabrales (Cares area)"
    },
    {
        "name": "Valdesquí",
        "tag": "1 Mar",
        "lat": 40.8989, "lon": -3.8875,
        "dateFrom": "2026-03-01", "dateTo": "2026-03-01",
        "wind": True, "snow": True,
        "forecastUrl": "https://www.accuweather.com/en/es/rascafria/305923/daily-weather-forecast/305923",
        "forecastName": "AccuWeather — Rascafría (Valdesquí)"
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

print("Fetching current data...")
data = fetch(f"{BASE_URL}/api/data?chat_id={CHAT_ID}")

data["wxLocations"] = WX_LOCATIONS

print("Saving...")
result = post(f"{BASE_URL}/api/data?chat_id={CHAT_ID}", data)
print("Done:", result)
print(f"\n{len(WX_LOCATIONS)} weather locations set:")
for loc in WX_LOCATIONS:
    print(f"  • {loc['name']} ({loc['dateFrom']} → {loc['dateTo']})")
