#!/usr/bin/env python3
"""
Populate tripobot Info Board with key resources for the Spain trip.

Usage:
  python3 populate_info.py
"""
import json, sys, urllib.request

BASE_URL = "https://tripobot-production.up.railway.app"  # ← paste your Railway URL here
CHAT_ID  = "-1003724580501"

# ── Categories ──────────────────────────────────────────────────────────────
CATS = [
    {"id": "cat_weather",   "icon": "🌦️", "label": "Weather"},
    {"id": "cat_maps",      "icon": "🗺️",  "label": "Navigation"},
    {"id": "cat_hiking",    "icon": "🥾",  "label": "Hiking"},
    {"id": "cat_skiing",    "icon": "⛷️",  "label": "Skiing"},
    {"id": "cat_logistics", "icon": "🚗",  "label": "Logistics"},
]

# ── Refs ─────────────────────────────────────────────────────────────────────
REFS = [
    # ── Weather ──
    {
        "id": "ref_w_madrid", "cat": "cat_weather", "type": "link",
        "name": "Madrid — AccuWeather",
        "url":  "https://www.accuweather.com/en/es/madrid/308526/daily-weather-forecast/308526",
    },
    {
        "id": "ref_w_burgos", "cat": "cat_weather", "type": "link",
        "name": "Burgos — AccuWeather",
        "url":  "https://www.accuweather.com/en/es/burgos/307142/daily-weather-forecast/307142",
    },
    {
        "id": "ref_w_picos", "cat": "cat_weather", "type": "link",
        "name": "Arenas de Cabrales / Picos — AccuWeather",
        "url":  "https://www.accuweather.com/en/es/arenas/2323185/daily-weather-forecast/2323185",
    },
    {
        "id": "ref_w_valdeskui", "cat": "cat_weather", "type": "link",
        "name": "Rascafría / Valdesquí — AccuWeather",
        "url":  "https://www.accuweather.com/en/es/rascafria/305923/daily-weather-forecast/305923",
    },

    # ── Maps / Navigation ──
    {
        "id": "ref_m_burgos", "cat": "cat_maps", "type": "link",
        "name": "Burgos city centre",
        "url":  "https://www.google.com/maps/search/?api=1&query=Burgos+Spain",
    },
    {
        "id": "ref_m_poncebos", "cat": "cat_maps", "type": "link",
        "name": "Poncebos trailhead (Cares start)",
        "url":  "https://www.google.com/maps/search/?api=1&query=Poncebos+Asturias+Spain",
    },
    {
        "id": "ref_m_cain", "cat": "cat_maps", "type": "link",
        "name": "Caín village (Cares end point)",
        "url":  "https://www.google.com/maps/search/?api=1&query=Cain+Leon+Spain",
    },
    {
        "id": "ref_m_arenas", "cat": "cat_maps", "type": "link",
        "name": "Arenas de Cabrales (accommodation area)",
        "url":  "https://www.google.com/maps/search/?api=1&query=Arenas+de+Cabrales+Asturias+Spain",
    },
    {
        "id": "ref_m_covadonga", "cat": "cat_maps", "type": "link",
        "name": "Lagos de Covadonga",
        "url":  "https://www.google.com/maps/search/?api=1&query=Lagos+de+Covadonga+Asturias+Spain",
    },
    {
        "id": "ref_m_cangas", "cat": "cat_maps", "type": "link",
        "name": "Cangas de Onís (lunch town)",
        "url":  "https://www.google.com/maps/search/?api=1&query=Cangas+de+Onis+Asturias+Spain",
    },
    {
        "id": "ref_m_valdeskui", "cat": "cat_maps", "type": "link",
        "name": "Valdesquí ski resort",
        "url":  "https://www.google.com/maps/search/?api=1&query=Valdesqui+ski+resort+Madrid+Spain",
    },

    # ── Hiking ──
    {
        "id": "ref_h_cares_alltrails", "cat": "cat_hiking", "type": "link",
        "name": "Ruta del Cares — AllTrails",
        "url":  "https://www.alltrails.com/trail/spain/asturias/ruta-del-cares",
    },
    {
        "id": "ref_h_covadonga_alltrails", "cat": "cat_hiking", "type": "link",
        "name": "Lagos de Covadonga loop — AllTrails",
        "url":  "https://www.alltrails.com/trail/spain/asturias/lagos-de-covadonga",
    },
    {
        "id": "ref_h_pnp", "cat": "cat_hiking", "type": "link",
        "name": "Picos de Europa National Park (official)",
        "url":  "https://www.parquenacionalpicosdeeuropa.es/",
    },
    {
        "id": "ref_h_notes", "cat": "cat_hiking", "type": "note",
        "name": "Cares trail notes",
        "content": (
            "Ruta del Cares: Poncebos → Caín\n"
            "Distance: ~11km one way (22km return)\n"
            "Elevation gain: ~500m\n"
            "Difficulty: moderate — rocky, narrow gorge path\n"
            "No shade → start early, bring 2L+ water\n"
            "Caín has a bar/restaurant for lunch\n"
            "Return is same path — budget same time"
        ),
    },

    # ── Skiing ──
    {
        "id": "ref_s_valdeskui", "cat": "cat_skiing", "type": "link",
        "name": "Valdesquí — Official site",
        "url":  "https://www.valdesqui.es/",
    },
    {
        "id": "ref_s_snow", "cat": "cat_skiing", "type": "link",
        "name": "Valdesquí — Snow conditions",
        "url":  "https://www.valdesqui.es/informacion-de-la-estacion/",
    },
    {
        "id": "ref_s_notes", "cat": "cat_skiing", "type": "note",
        "name": "Valdesquí notes",
        "content": (
            "Ticket office opens: 08:30\n"
            "Slopes open: 09:00\n"
            "Buy forfait (day pass) at the window or online\n"
            "Drive from Picos: ~4h (leave 04:00 → arrive ~08:15)\n"
            "Drive back to Madrid: ~1h10 via M-604"
        ),
    },

    # ── Logistics ──
    {
        "id": "ref_l_tolls", "cat": "cat_logistics", "type": "link",
        "name": "Spain toll calculator (via-t.com)",
        "url":  "https://www.via-t.com/",
    },
    {
        "id": "ref_l_dgt", "cat": "cat_logistics", "type": "link",
        "name": "Spain live traffic (DGT)",
        "url":  "https://infocar.dgt.es/etraffic/",
    },
    {
        "id": "ref_l_notes", "cat": "cat_logistics", "type": "note",
        "name": "Key numbers & drives",
        "content": (
            "Emergency: 112\n"
            "Police: 091\n"
            "Guardia Civil: 062\n"
            "\n"
            "Madrid → Burgos: ~2h30 (A-1 Norte)\n"
            "Burgos → Arenas de Cabrales: ~3h (A-67 / N-621)\n"
            "Arenas → Lagos Covadonga: ~30min\n"
            "Arenas → Valdesquí: ~4h (A-66 / A-6)\n"
            "Valdesquí → Madrid: ~1h10 (M-604 / A-6)\n"
            "\n"
            "Fuel up leaving Madrid (before A-1)\n"
            "Check toll requirements — rental may have Via-T"
        ),
    },
]

# ─────────────────────────────────────────────────────────────────────────────

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

def main():
    if "YOUR-APP" in BASE_URL:
        print("❌  Edit BASE_URL at the top of the script first.")
        sys.exit(1)

    print(f"Fetching data for chat {CHAT_ID}...")
    data = fetch(f"{BASE_URL}/api/data?chat_id={CHAT_ID}")

    existing_cat_ids = {c["id"] for c in (data.get("refCats") or [])}
    existing_ref_ids = {r["id"] for r in (data.get("refs")    or [])}

    data.setdefault("refCats", [])
    data.setdefault("refs",    [])

    added_cats = added_refs = 0
    for cat in CATS:
        if cat["id"] not in existing_cat_ids:
            data["refCats"].append(cat)
            added_cats += 1

    for ref in REFS:
        if ref["id"] not in existing_ref_ids:
            data["refs"].append(ref)
            added_refs += 1

    print(f"Saving — +{added_cats} categories, +{added_refs} refs...")
    post(f"{BASE_URL}/api/data?chat_id={CHAT_ID}", data)
    print("✅  Done. Open the Info Board tab to see your resources.")

if __name__ == "__main__":
    main()
