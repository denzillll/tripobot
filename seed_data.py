#!/usr/bin/env python3
"""
seed_data.py — populate Picos de Europa trip data for tripobot.

Usage
-----
# Local dev — writes to data.json (chatId='default' in the browser)
python seed_data.py

# Production — writes to data/trip_<id>.json for a real Telegram group chat
python seed_data.py --chat-id -1001234567890

# On Railway
railway run python seed_data.py --chat-id -1001234567890

How to find your chat ID
------------------------
1. Add the bot to your group chat.
2. Send /myid in that group — the bot replies with both your user ID and the chat ID.
3. Use the chat ID (a negative number like -1001234567890) as --chat-id.
"""

import json, re, argparse
from pathlib import Path

# ── helpers (mirrors main.py) ──────────────────────────────────────────────────

def _safe_id(chat_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]", "_", str(chat_id))

def data_file(chat_id: str) -> Path:
    if str(chat_id) == "default":
        return Path("data.json")
    Path("data").mkdir(exist_ok=True)
    return Path("data") / f"trip_{_safe_id(chat_id)}.json"

# ── trip data ──────────────────────────────────────────────────────────────────
# Edit this block freely — it's just a Python dict.

TRIP_DATA = {
    "trip": {
        "name":  "Picos de Europa + Valdesqui",
        "dates": "26 Feb – 1 Mar 2026"
    },

    # ── Itinerary days ────────────────────────────────────────────────────────
    "days": [
        {
            "id": "thu", "emoji": "🚗",
            "label": "Thu 26 Feb", "title": "Madrid to Burgos",
            "date": "2026-02-26",
            "description": "Pick up rental car and head north. ~3 hrs on A-1.",
            "stops": [
                {"time": "20:00", "name": "Leave Madrid",
                 "note": "Collect rental car, fill up fuel, head north on A-1 toward Burgos (~3 hrs).",
                 "mapsUrl": ""},
                {"time": "23:00", "name": "Burgos – overnight stop",
                 "note": "Sleep here. Continue to Picos at 7 AM Friday.",
                 "mapsUrl": ""}
            ]
        },
        {
            "id": "fri", "emoji": "🥾",
            "label": "Fri 27 Feb", "title": "Arrive Picos + Ruta del Cares",
            "date": "2026-02-27",
            "description": "The big hike day. Start early, bring plenty of water.",
            "stops": [
                {"time": "07:00", "name": "Drive Burgos → Arenas de Cabrales",
                 "note": "~3 hrs via A-67 and AS-114.",
                 "mapsUrl": ""},
                {"time": "10:30", "name": "Ruta del Cares",
                 "note": "Poncebos to Caín and back, 24 km, 6–7 hrs. Rockfall warning active. Bring 2L+ water.",
                 "mapsUrl": "https://www.alltrails.com/trail/spain/asturias/pr-pnpe-3-ruta-del-cares--2"},
                {"time": "17:30", "name": "Back to accommodation",
                 "note": "Rest, dinner in Arenas.",
                 "mapsUrl": ""}
            ]
        },
        {
            "id": "sat", "emoji": "🏔",
            "label": "Sat 28 Feb", "title": "Lagos de Covadonga",
            "date": "2026-02-28",
            "description": "Easy lake loop. Sleep early — 3:45 AM alarm tomorrow.",
            "stops": [
                {"time": "08:30", "name": "Drive to Lagos de Covadonga",
                 "note": "~30 min from Arenas.",
                 "mapsUrl": ""},
                {"time": "09:00", "name": "Los Lagos Circuit",
                 "note": "6 km easy loop, 2–2.5 hrs.",
                 "mapsUrl": ""},
                {"time": "12:00", "name": "Lunch in Cangas de Onís",
                 "note": "Good restaurants, 20 min from the lakes.",
                 "mapsUrl": ""},
                {"time": "14:00", "name": "Back at accom – REST",
                 "note": "Sleep early! Alarm 3:45 AM. Pack for ski day tonight.",
                 "mapsUrl": ""}
            ]
        },
        {
            "id": "sun", "emoji": "⛷️",
            "label": "Sun 1 Mar", "title": "Valdesqui + Drive Home",
            "date": "2026-03-01",
            "description": "Ski / snowboard day, then drive back to Madrid.",
            "stops": [
                {"time": "04:00", "name": "Drive Picos → Valdesqui",
                 "note": "~4 h 15 min — share driving.",
                 "mapsUrl": ""},
                {"time": "09:00", "name": "Valdesqui snowboarding",
                 "note": "Opens 9 AM. Buy forfait online in advance!",
                 "mapsUrl": "https://www.valdesqui.es"},
                {"time": "17:00", "name": "Drive back to Madrid",
                 "note": "1 h 10 min. Return car by 23:30.",
                 "mapsUrl": ""}
            ]
        }
    ],

    # ── Accommodations (add yours here) ───────────────────────────────────────
    "accoms": [
        # Example — fill in real details:
        # {
        #     "name": "Airbnb Arenas de Cabrales",
        #     "url": "https://airbnb.com/rooms/...",
        #     "checkin": "2026-02-27", "checkinTime": "15:00",
        #     "checkout": "2026-03-01", "checkoutTime": "11:00",
        #     "day": "27 Feb 15:00 – 1 Mar 11:00",
        #     "mapsUrl": "",
        #     "notes": "Key box, code 1234. Free parking."
        # }
    ],

    # ── Weather links (legacy, kept for migration) ────────────────────────────
    "weather": [
        {"name": "Picos de Europa",
         "url": "https://www.accuweather.com/en/es/picos-de-europa/94802_poi/weather-forecast/94802_poi",
         "day": "Fri–Sat"},
        {"name": "Arenas de Cabrales (detailed)",
         "url": "https://www.meteoblue.com/en/weather/week/las-arenas-de-cabrales_spain_3119030",
         "day": "Fri–Sat"},
        {"name": "Burgos",
         "url": "https://www.accuweather.com/en/es/burgos/305514/daily-weather-forecast/305514",
         "day": "Thu"},
        {"name": "Valdesqui snow report",
         "url": "https://www.valdesqui.es/en/snow-report/",
         "day": "Sun"}
    ],

    # ── Weather forecast locations (for the in-app weather widget) ────────────
    "wxLocations": [
        {
            "name": "Burgos", "tag": "Thu 26",
            "lat": 42.3439, "lon": -3.6969,
            "dateFrom": "2026-02-26", "dateTo": "2026-02-26",
            "wind": False, "snow": False,
            "forecastUrl": "https://www.accuweather.com/en/es/burgos/305514/daily-weather-forecast/305514",
            "forecastName": "AccuWeather Burgos"
        },
        {
            "name": "Picos de Europa", "tag": "Fri 27–Sat 28",
            "lat": 43.2520, "lon": -4.8492,
            "dateFrom": "2026-02-27", "dateTo": "2026-02-28",
            "wind": True, "snow": False,
            "forecastUrl": "https://www.meteoblue.com/en/weather/week/las-arenas-de-cabrales_spain_3119030",
            "forecastName": "Meteoblue Arenas de Cabrales"
        },
        {
            "name": "Valdesqui", "tag": "Sun 1",
            "lat": 40.8897, "lon": -3.9153,
            "dateFrom": "2026-03-01", "dateTo": "2026-03-01",
            "wind": False, "snow": True,
            "forecastUrl": "https://www.valdesqui.es/en/snow-report/",
            "forecastName": "Valdesqui snow report"
        }
    ],

    # ── References ────────────────────────────────────────────────────────────
    "refCats": [
        {"id": "trail",   "label": "Trail Status", "icon": "🥾"},
        {"id": "booking", "label": "Bookings",     "icon": "🎫"}
    ],
    "refs": [
        {"name": "Park Trail Status (EN)",
         "url": "https://parquenacionalpicoseuropa.es/english/plan-your-visit/",
         "cat": "trail", "type": "link", "notes": "Check rockfall warnings before Cares"},
        {"name": "AEMET Mountain Forecast",
         "url": "https://www.aemet.es/en/eltiempo/prediccion/montana",
         "cat": "trail", "type": "link", "notes": "Official Spanish met office"},
        {"name": "Ruta del Cares – AllTrails",
         "url": "https://www.alltrails.com/trail/spain/asturias/pr-pnpe-3-ruta-del-cares--2",
         "cat": "trail", "type": "link", "notes": "24 km, 6–7 hrs"},
        {"name": "Valdesqui Forfait",
         "url": "https://www.valdesqui.es",
         "cat": "booking", "type": "link", "notes": "Buy online — cheaper + skip queue"}
    ],

    # ── Emergency numbers ─────────────────────────────────────────────────────
    "emergency": [
        {"name": "Spain Emergency",             "number": "112"},
        {"name": "Asturias Mountain Rescue",    "number": "985 848 614"},
        {"name": "Cantabria Mountain Rescue",   "number": "942 748 555"},
        {"name": "Civil Guard",                 "number": "062"}
    ],

    # ── Group packing checklist ───────────────────────────────────────────────
    "groupChecklist": [
        {
            "id": "hiking", "label": "Hiking Gear", "icon": "🥾",
            "items": [
                "Ankle-support hiking boots",
                "2L+ water (no refills on Cares)",
                "Packed lunch + snacks",
                "Waterproof jacket",
                "Warm mid-layer",
                "Beanie + buff",
                "Sunscreen + sunglasses",
                "Offline maps downloaded (Maps.me / AllTrails)",
                "First aid + blister kit"
            ]
        },
        {
            "id": "snowboard", "label": "Snowboard Gear", "icon": "⛷️",
            "items": [
                "Board or skis",
                "Helmet",
                "Goggles",
                "Gloves",
                "Ski jacket + pants",
                "Thermal base layers",
                "Ski socks ×2",
                "Forfait booked online"
            ]
        },
        {
            "id": "admin", "label": "Trip Admin", "icon": "🚗",
            "items": [
                "Rental car confirmed",
                "All accoms booked",
                "Cash for rural areas",
                "Spain SIM / roaming on",
                "Fuel up before leaving Madrid"
            ]
        }
    ],
    "groupProgress": {},

    # ── Admins (Telegram user IDs who can edit) ───────────────────────────────
    # Add your user ID here to be the only admin, or leave empty for everyone to edit.
    # Get your ID with /myid in the Telegram bot.
    "admins": []
}

# ── main ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Seed Picos de Europa trip data into tripobot.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        "--chat-id", default="default", metavar="ID",
        help="Telegram chat ID (default: 'default' → writes data.json)"
    )
    parser.add_argument(
        "--force", action="store_true",
        help="Overwrite without confirmation if the file already exists"
    )
    args = parser.parse_args()

    fpath = data_file(args.chat_id)

    if fpath.exists() and not args.force:
        ans = input(f"⚠️  {fpath} already exists. Overwrite? [y/N] ").strip().lower()
        if ans != "y":
            print("Aborted.")
            return

    with open(fpath, "w", encoding="utf-8") as f:
        json.dump(TRIP_DATA, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Written → {fpath}")
    print(f"  Trip   : {TRIP_DATA['trip']['name']}")
    print(f"  Days   : {len(TRIP_DATA['days'])}")
    print(f"  Refs   : {len(TRIP_DATA['refs'])}")
    print(f"  Checklist categories : {len(TRIP_DATA['groupChecklist'])}")
    print(f"  Emergency numbers    : {len(TRIP_DATA['emergency'])}")


if __name__ == "__main__":
    main()
