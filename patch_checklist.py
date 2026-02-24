#!/usr/bin/env python3
"""
Patch groupChecklist for Morocco trip.
Run: python3 patch_checklist.py
"""
import json, urllib.request

CHAT_ID  = "-5046151729"
BASE_URL = "https://tripobot-production.up.railway.app"

GROUP_CHECKLIST = []

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

data["groupChecklist"] = GROUP_CHECKLIST
data["groupProgress"]  = {}   # clear any previous ticks

print("Saving...")
result = post(f"{BASE_URL}/api/data?chat_id={CHAT_ID}", data)
print("Done:", result)
print(f"\n{len(GROUP_CHECKLIST)} categories:")
for cat in GROUP_CHECKLIST:
    print(f"  {cat['icon']} {cat['label']} — {len(cat['items'])} items")
