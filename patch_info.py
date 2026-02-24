#!/usr/bin/env python3
"""
Patch refs (Info tab) for Morocco trip.
Run: python3 patch_info.py
"""
import json, urllib.request

CHAT_ID  = "-5046151729"
BASE_URL = "https://tripobot-production.up.railway.app"

REF_CATS = [
    {"id": "cat-emergency",  "icon": "🚨", "label": "Emergency"},
    {"id": "cat-sahara",     "icon": "🏜️", "label": "Sahara Tour"},
    {"id": "cat-marrakech",  "icon": "🕌", "label": "Marrakech"},
    {"id": "cat-transport",  "icon": "🚕", "label": "Transport"},
]

REFS = [
    # ── Emergency ──────────────────────────────────────────────────────────────
    {
        "id": "ref-emerg-numbers",
        "catId": "cat-emergency",
        "type": "note",
        "title": "Morocco Emergency Numbers",
        "content": (
            "Police: 190\n"
            "Ambulance / Fire: 150\n"
            "Gendarmerie (rural): 177\n"
            "Emergency (mobile): 112\n"
            "\n"
            "Tourist Police Marrakech: +212 524 38 46 01\n"
            "(Near Jemaa el-Fnaa, by Koutoubia Mosque)"
        )
    },
    {
        "id": "ref-emerg-sg",
        "catId": "cat-emergency",
        "type": "note",
        "title": "Singapore — MFA Emergency",
        "content": (
            "MFA Duty Office (24hr): +65 6379 8800 / 8855\n"
            "Email: mfa@mfa.gov.sg\n"
            "\n"
            "Nearest mission: Consulate General, Casablanca\n"
            "No Singapore embassy in Rabat — use MFA hotline\n"
            "\n"
            "For: lost passport, arrest, hospitalisation, death"
        )
    },

    # ── Sahara Tour ────────────────────────────────────────────────────────────
    {
        "id": "ref-tour-info",
        "catId": "cat-sahara",
        "type": "note",
        "title": "Sahara Tour — Key Info",
        "content": (
            "Pickup: 7:00am, 5 Mar 2026 (hotel lobby)\n"
            "Dropoff: 8:00pm, 7 Mar 2026\n"
            "Route: Marrakech → Tinghir → Merzouga → Marrakech\n"
            "Includes: transport, Hotel Saghro (Tinghir), desert camp,\n"
            "camel ride, breakfast & dinner throughout"
        )
    },
    {
        "id": "ref-tour-contact",
        "catId": "cat-sahara",
        "type": "note",
        "title": "Tour Operator Contact",
        "content": (
            "Operator: [ADD OPERATOR NAME]\n"
            "Phone / WhatsApp: [ADD NUMBER]\n"
            "Booking ref: [ADD REF]\n"
            "Email: [ADD EMAIL]"
        )
    },

    # ── Marrakech ──────────────────────────────────────────────────────────────
    {
        "id": "ref-mkech-tips",
        "catId": "cat-marrakech",
        "type": "note",
        "title": "Marrakech Tips",
        "content": (
            "Currency: Moroccan Dirham (MAD)\n"
            "~1 GBP ≈ 13 MAD  |  ~1 AUD ≈ 6 MAD  |  ~1 EUR ≈ 11 MAD\n"
            "ATMs at airport & city centre — use bank ATMs, avoid standalone\n"
            "\n"
            "Haggling: expected in souks, start at ~40% of asking price\n"
            "Tipping: 10–20 MAD for guides/helpers, 10% in restaurants\n"
            "\n"
            "Dress code: cover shoulders & knees in medina/mosques\n"
            "Tap water: NOT safe to drink — buy bottled"
        )
    },
    {
        "id": "ref-mkech-phrases",
        "catId": "cat-marrakech",
        "type": "note",
        "title": "Useful Phrases (Darija / French)",
        "content": (
            "Hello: Salam / Bonjour\n"
            "Thank you: Shukran / Merci\n"
            "No thank you: La shukran / Non merci\n"
            "How much?: Bshhal? / C'est combien?\n"
            "Too expensive: Ghali bezzaf / C'est trop cher\n"
            "Water please: Lma afak / De l'eau s'il vous plaît\n"
            "Where is...?: Fin kayn...? / Où est...?\n"
            "Yes / No: Iyeh / La"
        )
    },

    # ── Transport ──────────────────────────────────────────────────────────────
    {
        "id": "ref-transport",
        "catId": "cat-transport",
        "type": "note",
        "title": "Getting Around Marrakech",
        "content": (
            "Airport → City: Petit taxi, fixed ~100–150 MAD (agree before)\n"
            "City taxis: Petit taxi (red) — meter or agree price first\n"
            "Grand taxi: shared long-distance taxis\n"
            "Ride apps: inDriver & Careem work in Marrakech\n"
            "Medina: walk only — cars/bikes can't enter most streets\n"
            "\n"
            "Airport: Marrakech Menara (RAK)\n"
            "~15 min drive from city centre"
        )
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

data["refCats"] = REF_CATS
data["refs"]    = REFS

print("Saving...")
result = post(f"{BASE_URL}/api/data?chat_id={CHAT_ID}", data)
print("Done:", result)
print(f"\n{len(REF_CATS)} categories, {len(REFS)} items:")
for cat in REF_CATS:
    items = [r["title"] for r in REFS if r["catId"] == cat["id"]]
    for t in items:
        print(f"  {cat['icon']} {t}")
