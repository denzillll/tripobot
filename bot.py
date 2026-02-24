"""
TripBot — Picos de Europa + Valdesquí Trip Assistant
A Telegram bot to manage trip info, accommodations, weather links, and more.
"""

import json
import os
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters, ConversationHandler
)

# ── Logging ──────────────────────────────────────────────────────────────────
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ── Config ───────────────────────────────────────────────────────────────────
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATA_FILE = Path("data.json")

# ── Data helpers ─────────────────────────────────────────────────────────────
def load_data() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return get_default_data()

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_default_data() -> dict:
    return {
        "trip": {
            "name": "Picos de Europa + Valdesquí",
            "dates": "26 Feb – 1 Mar 2026",
            "group": []
        },
        "days": [
            {
                "id": "thu",
                "label": "Thu 26 Feb",
                "title": "Madrid → Burgos",
                "emoji": "🚗",
                "stops": [
                    {"time": "20:00", "name": "Leave Madrid", "note": "Pick up rental car, fill up fuel, head north on A-1 toward Burgos (~3hrs)"},
                    {"time": "~23:00", "name": "Burgos overnight stop", "note": "Sleep here, continue to Picos at ~7am Friday (~3hrs drive)"}
                ]
            },
            {
                "id": "fri",
                "label": "Fri 27 Feb",
                "title": "Arrive Picos + Ruta del Cares",
                "emoji": "🥾",
                "stops": [
                    {"time": "07:00", "name": "Drive Burgos → Arenas de Cabrales", "note": "~3hrs via A-67 + AS-114, arrive ~10am"},
                    {"time": "10:30", "name": "🥾 Ruta del Cares (PR-PNPE-3)", "note": "Poncebos → Caín → back = 24km, 6–7hrs. ⚠️ Rockfall warning active. Bring 2L+ water, hiking boots, lunch."},
                    {"time": "~17:30", "name": "Back to accommodation", "note": "Rest, dinner in Arenas de Cabrales"}
                ]
            },
            {
                "id": "sat",
                "label": "Sat 28 Feb",
                "title": "Lagos de Covadonga — Back by 3PM",
                "emoji": "🏔",
                "stops": [
                    {"time": "08:30", "name": "Drive to Lagos de Covadonga", "note": "~30min from Arenas, can drive up freely in winter"},
                    {"time": "09:00", "name": "🥾 PR-PNPE-2 Los Lagos Circuit", "note": "6km, 2–2.5hrs easy circuit around Lago Enol & Lago Ercina"},
                    {"time": "12:00", "name": "Lunch in Cangas de Onís", "note": "20min from lakes, good restaurants"},
                    {"time": "14:00", "name": "⚠️ Back at accom — REST", "note": "Sleep early! Set alarm 3:45AM. Pack tonight."}
                ]
            },
            {
                "id": "sun",
                "label": "Sun 1 Mar",
                "title": "Valdesquí + Drive Home",
                "emoji": "⛷️",
                "stops": [
                    {"time": "04:00", "name": "Drive Picos → Valdesquí", "note": "~4h 15min, share driving, coffee stop at Palencia"},
                    {"time": "09:00", "name": "⛷️ Valdesquí — Opens 9AM", "note": "Buy forfait online in advance. Parking fills fast on Sundays."},
                    {"time": "~17:00", "name": "Drive back to Madrid", "note": "1h 10min. Return rental car by 23:30."}
                ]
            }
        ],
        "accoms": [],
        "weather": [
            {"name": "Picos de Europa (AccuWeather)", "url": "https://www.accuweather.com/en/es/picos-de-europa/94802_poi/weather-forecast/94802_poi", "day": "Fri–Sat"},
            {"name": "Arenas de Cabrales (Meteoblue)", "url": "https://www.meteoblue.com/en/weather/week/las-arenas-de-cabrales_spain_3119030", "day": "Fri–Sat"},
            {"name": "Burgos (AccuWeather)", "url": "https://www.accuweather.com/en/es/burgos/305514/daily-weather-forecast/305514", "day": "Thu"},
            {"name": "Valdesquí Snow Report", "url": "https://www.valdesqui.es/en/snow-report/", "day": "Sunday"}
        ],
        "links": [
            {"name": "🔴 Park Trail Status (EN)", "url": "https://parquenacionalpicoseuropa.es/english/plan-your-visit/", "category": "trail"},
            {"name": "🔴 Park Trail Status (ES)", "url": "https://parquenacionalpicoseuropa.es/planifica-tu-visita/", "category": "trail"},
            {"name": "⛰ AEMET Mountain Forecast", "url": "https://www.aemet.es/en/eltiempo/prediccion/montana?w=0&datos=det&s=picos", "category": "trail"},
            {"name": "📍 Ruta del Cares (AllTrails)", "url": "https://www.alltrails.com/trail/spain/asturias/pr-pnpe-3-ruta-del-cares--2", "category": "trail"},
            {"name": "🎫 Valdesquí Forfait", "url": "https://www.valdesqui.es", "category": "booking"}
        ],
        "emergency": [
            {"name": "Spain Emergency", "number": "112"},
            {"name": "Asturias Mountain Rescue (GREIM)", "number": "985 848 614"},
            {"name": "Cantabria Mountain Rescue", "number": "942 748 555"},
            {"name": "Civil Guard", "number": "062"}
        ],
        "checklist": {
            "hiking": ["Ankle-support hiking boots", "2L+ water (no refills on Cares trail)", "Packed lunch + snacks", "Waterproof jacket", "Warm mid-layer", "Beanie + buff", "Sunscreen + sunglasses", "Offline maps downloaded (Google Maps / AllTrails)", "First aid kit + blister plasters"],
            "snowboard": ["Board or skis", "Helmet", "Goggles", "Gloves", "Ski jacket + pants", "Base layers (thermal)", "Ski socks x2", "Forfait booked online ✓"],
            "admin": ["Rental car confirmed", "All accoms booked", "Cash (rural places may be cash-only)", "Spain SIM / roaming enabled", "Car drop-off location confirmed", "Fuel up before leaving Madrid"]
        },
        "admins": []
    }

# ── Auth helper ───────────────────────────────────────────────────────────────
def is_admin(user_id: int, data: dict) -> bool:
    return len(data["admins"]) == 0 or user_id in data["admins"]

# ── /start ────────────────────────────────────────────────────────────────────
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    text = (
        f"🏔 *{data['trip']['name']}*\n"
        f"📅 {data['trip']['dates']}\n\n"
        "Your trip assistant is live\\! Here's what I can do:\n\n"
        "📋 `/itinerary` — full day\\-by\\-day plan\n"
        "🏨 `/accoms` — accommodation links\n"
        "🌤 `/weather` — weather forecast links\n"
        "🔗 `/links` — trail status \\+ key links\n"
        "🚨 `/emergency` — emergency numbers\n"
        "✅ `/checklist` — packing list\n\n"
        "⚙️ *Admin commands:*\n"
        "`/addaccom` — add a booking\n"
        "`/removeaccom` — remove a booking\n"
        "`/addweather` — add weather link\n"
        "`/addlink` — add a key link\n"
        "`/addstop` — add itinerary stop\n"
        "`/edittrip` — edit trip name/dates\n\n"
        "Type `/help` for the full command list\\."
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2")

# ── /help ─────────────────────────────────────────────────────────────────────
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "🤖 *TripBot Commands*\n\n"
        "*View info:*\n"
        "/itinerary — full itinerary\n"
        "/day\\_thu, /day\\_fri, /day\\_sat, /day\\_sun — specific day\n"
        "/accoms — accommodations\n"
        "/weather — weather links\n"
        "/links — trail status \\+ key links\n"
        "/emergency — emergency numbers\n"
        "/checklist — packing checklist\n\n"
        "*Admin \\(edit\\):*\n"
        "/addaccom \\[name\\] \\| \\[link\\] \\| \\[day\\] — add booking\n"
        "/removeaccom — show list to remove\n"
        "/addweather \\[name\\] \\| \\[url\\] \\| \\[day\\] — add forecast link\n"
        "/addlink \\[name\\] \\| \\[url\\] \\| \\[category\\] — add key link\n"
        "/addstop \\[day\\_id\\] \\| \\[time\\] \\| \\[name\\] \\| \\[note\\] — add itinerary stop\n"
        "/edittrip \\[name\\] \\| \\[dates\\] — update trip details\n\n"
        "*Examples:*\n"
        "`/addaccom Airbnb Arenas | https://airbnb.com/rooms/... | Fri–Sat`\n"
        "`/addstop fri | 20:00 | Dinner at La Sidrería | Try the local cider!`"
    )
    await update.message.reply_text(text, parse_mode="MarkdownV2")

# ── /itinerary ────────────────────────────────────────────────────────────────
async def itinerary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    keyboard = []
    for day in data["days"]:
        keyboard.append([InlineKeyboardButton(
            f"{day['emoji']} {day['label']} — {day['title']}",
            callback_data=f"day_{day['id']}"
        )])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"📋 *{data['trip']['name']}*\n_{data['trip']['dates']}_\n\nPick a day:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def day_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    day_id = query.data.replace("day_", "")
    data = load_data()
    day = next((d for d in data["days"] if d["id"] == day_id), None)
    if not day:
        await query.edit_message_text("Day not found.")
        return
    lines = [f"{day['emoji']} *{day['label']} — {day['title']}*\n"]
    for stop in day["stops"]:
        lines.append(f"⏰ `{stop['time']}`  *{stop['name']}*")
        if stop.get("note"):
            lines.append(f"   _{stop['note']}_")
        lines.append("")
    await query.edit_message_text("\n".join(lines), parse_mode="Markdown")

# Shortcut /day_xxx commands
async def day_direct(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text.lstrip("/").split("@")[0]
    day_id = command.replace("day_", "")
    data = load_data()
    day = next((d for d in data["days"] if d["id"] == day_id), None)
    if not day:
        await update.message.reply_text("Day not found. Try /itinerary")
        return
    lines = [f"{day['emoji']} *{day['label']} — {day['title']}*\n"]
    for stop in day["stops"]:
        lines.append(f"⏰ `{stop['time']}`  *{stop['name']}*")
        if stop.get("note"):
            lines.append(f"   _{stop['note']}_")
        lines.append("")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

# ── /accoms ───────────────────────────────────────────────────────────────────
async def accoms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data["accoms"]:
        await update.message.reply_text(
            "🏨 *Accommodations*\n\nNo bookings added yet\\.\n\n"
            "Add one with:\n`/addaccom Name | https://link.com | Day`\n\n"
            "Example:\n`/addaccom Airbnb Arenas | https://airbnb.com/rooms/123 | Fri–Sat`",
            parse_mode="MarkdownV2"
        )
        return
    lines = ["🏨 *Accommodations*\n"]
    for i, a in enumerate(data["accoms"]):
        lines.append(f"*{i+1}\\. {escape_md(a['name'])}*")
        if a.get("day"):
            lines.append(f"   📅 {escape_md(a['day'])}")
        lines.append(f"   🔗 [Open booking]({a['url']})")
        if a.get("notes"):
            lines.append(f"   _{escape_md(a['notes'])}_")
        lines.append("")
    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2", disable_web_page_preview=True)

# ── /weather ──────────────────────────────────────────────────────────────────
async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    lines = ["🌤 *Weather Forecasts*\n"]
    for w in data["weather"]:
        day_str = f" \\({escape_md(w['day'])}\\)" if w.get("day") else ""
        lines.append(f"• [{escape_md(w['name'])}]({w['url']}){day_str}")
    lines.append("\n_Forecasts update daily — check the morning of each hike\\._")
    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2", disable_web_page_preview=True)

# ── /links ────────────────────────────────────────────────────────────────────
async def links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    trail_links = [l for l in data["links"] if l.get("category") == "trail"]
    booking_links = [l for l in data["links"] if l.get("category") == "booking"]
    other_links = [l for l in data["links"] if l.get("category") not in ("trail", "booking")]

    lines = ["🔗 *Key Links*\n"]
    if trail_links:
        lines.append("*Trail Status:*")
        for l in trail_links:
            lines.append(f"• [{escape_md(l['name'])}]({l['url']})")
        lines.append("")
    if booking_links:
        lines.append("*Bookings:*")
        for l in booking_links:
            lines.append(f"• [{escape_md(l['name'])}]({l['url']})")
        lines.append("")
    if other_links:
        lines.append("*Other:*")
        for l in other_links:
            lines.append(f"• [{escape_md(l['name'])}]({l['url']})")

    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2", disable_web_page_preview=True)

# ── /emergency ────────────────────────────────────────────────────────────────
async def emergency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    lines = ["🚨 *Emergency Numbers*\n"]
    for e in data["emergency"]:
        lines.append(f"*{escape_md(e['name'])}*\n`{e['number']}`\n")
    lines.append("_In any emergency in Spain, always call *112* first\\._")
    await update.message.reply_text("\n".join(lines), parse_mode="MarkdownV2")

# ── /checklist ────────────────────────────────────────────────────────────────
async def checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    keyboard = [
        [InlineKeyboardButton("🥾 Hiking Gear", callback_data="check_hiking")],
        [InlineKeyboardButton("⛷️ Snowboard Gear", callback_data="check_snowboard")],
        [InlineKeyboardButton("🚗 Trip Admin", callback_data="check_admin")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ *Packing Checklist*\n\nChoose a category:", reply_markup=reply_markup, parse_mode="Markdown")

async def checklist_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    category = query.data.replace("check_", "")
    data = load_data()
    items = data["checklist"].get(category, [])
    emoji_map = {"hiking": "🥾", "snowboard": "⛷️", "admin": "🚗"}
    title_map = {"hiking": "Hiking Gear", "snowboard": "Snowboard Gear", "admin": "Trip Admin"}
    lines = [f"{emoji_map.get(category, '✅')} *{title_map.get(category, category)} Checklist*\n"]
    for item in items:
        lines.append(f"☐ {item}")
    await query.edit_message_text("\n".join(lines), parse_mode="Markdown")

# ── Markdown escape ───────────────────────────────────────────────────────────
def escape_md(text: str) -> str:
    special = r"\_*[]()~`>#+-=|{}.!"
    for c in special:
        text = text.replace(c, f"\\{c}")
    return text

# ── ADMIN: /addaccom ──────────────────────────────────────────────────────────
async def addaccom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("⛔ Admin only.")
        return

    args = " ".join(context.args)
    parts = [p.strip() for p in args.split("|")]

    if len(parts) < 2:
        await update.message.reply_text(
            "Usage: `/addaccom Name | URL | Day (optional) | Notes (optional)`\n\n"
            "Example:\n`/addaccom Airbnb Arenas | https://airbnb.com/rooms/123 | Fri–Sat | Checkout 11am`",
            parse_mode="Markdown"
        )
        return

    accom = {
        "name": parts[0],
        "url": parts[1],
        "day": parts[2] if len(parts) > 2 else "",
        "notes": parts[3] if len(parts) > 3 else ""
    }
    data["accoms"].append(accom)
    save_data(data)
    await update.message.reply_text(
        f"✅ Added accommodation: *{accom['name']}*\n"
        f"📅 {accom['day'] or 'No day specified'}\n"
        f"🔗 {accom['url']}",
        parse_mode="Markdown"
    )

# ── ADMIN: /removeaccom ───────────────────────────────────────────────────────
async def removeaccom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("⛔ Admin only.")
        return
    if not data["accoms"]:
        await update.message.reply_text("No accommodations to remove.")
        return

    # If number provided directly
    if context.args and context.args[0].isdigit():
        idx = int(context.args[0]) - 1
        if 0 <= idx < len(data["accoms"]):
            removed = data["accoms"].pop(idx)
            save_data(data)
            await update.message.reply_text(f"🗑 Removed: *{removed['name']}*", parse_mode="Markdown")
        else:
            await update.message.reply_text("Invalid number.")
        return

    # Show list with inline buttons
    keyboard = []
    for i, a in enumerate(data["accoms"]):
        keyboard.append([InlineKeyboardButton(
            f"🗑 {a['name']} ({a.get('day', '')})",
            callback_data=f"delaccom_{i}"
        )])
    keyboard.append([InlineKeyboardButton("Cancel", callback_data="cancel")])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Which accommodation to remove?", reply_markup=reply_markup)

async def delaccom_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "cancel":
        await query.edit_message_text("Cancelled.")
        return
    data = load_data()
    if not is_admin(query.from_user.id, data):
        await query.edit_message_text("⛔ Admin only.")
        return
    idx = int(query.data.replace("delaccom_", ""))
    if 0 <= idx < len(data["accoms"]):
        removed = data["accoms"].pop(idx)
        save_data(data)
        await query.edit_message_text(f"🗑 Removed: *{removed['name']}*", parse_mode="Markdown")
    else:
        await query.edit_message_text("Not found.")

# ── ADMIN: /addweather ────────────────────────────────────────────────────────
async def addweather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("⛔ Admin only.")
        return
    args = " ".join(context.args)
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 2:
        await update.message.reply_text(
            "Usage: `/addweather Name | URL | Day`\n\n"
            "Example:\n`/addweather Potes forecast | https://accuweather.com/... | Fri`",
            parse_mode="Markdown"
        )
        return
    entry = {"name": parts[0], "url": parts[1], "day": parts[2] if len(parts) > 2 else ""}
    data["weather"].append(entry)
    save_data(data)
    await update.message.reply_text(f"✅ Added weather link: *{entry['name']}*", parse_mode="Markdown")

# ── ADMIN: /addlink ───────────────────────────────────────────────────────────
async def addlink(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("⛔ Admin only.")
        return
    args = " ".join(context.args)
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 2:
        await update.message.reply_text(
            "Usage: `/addlink Name | URL | category`\n"
            "Categories: `trail`, `booking`, `other`\n\n"
            "Example:\n`/addlink Park webcam | https://... | trail`",
            parse_mode="Markdown"
        )
        return
    entry = {"name": parts[0], "url": parts[1], "category": parts[2] if len(parts) > 2 else "other"}
    data["links"].append(entry)
    save_data(data)
    await update.message.reply_text(f"✅ Added link: *{entry['name']}*", parse_mode="Markdown")

# ── ADMIN: /addstop ───────────────────────────────────────────────────────────
async def addstop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("⛔ Admin only.")
        return
    args = " ".join(context.args)
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 3:
        await update.message.reply_text(
            "Usage: `/addstop day_id | time | name | note`\n"
            "Day IDs: `thu`, `fri`, `sat`, `sun`\n\n"
            "Example:\n`/addstop fri | 20:00 | Dinner at La Sidrería | Try the local cider!`",
            parse_mode="Markdown"
        )
        return
    day_id = parts[0].lower()
    day = next((d for d in data["days"] if d["id"] == day_id), None)
    if not day:
        await update.message.reply_text(f"Day ID not found: `{day_id}`. Use: thu, fri, sat, sun")
        return
    stop = {"time": parts[1], "name": parts[2], "note": parts[3] if len(parts) > 3 else ""}
    day["stops"].append(stop)
    save_data(data)
    await update.message.reply_text(
        f"✅ Added stop to *{day['label']}*:\n`{stop['time']}` — {stop['name']}",
        parse_mode="Markdown"
    )

# ── ADMIN: /edittrip ──────────────────────────────────────────────────────────
async def edittrip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("⛔ Admin only.")
        return
    args = " ".join(context.args)
    parts = [p.strip() for p in args.split("|")]
    if len(parts) < 2:
        await update.message.reply_text(
            "Usage: `/edittrip Trip Name | Dates`\n\n"
            "Example:\n`/edittrip Picos de Europa 2026 | 26 Feb – 1 Mar 2026`",
            parse_mode="Markdown"
        )
        return
    data["trip"]["name"] = parts[0]
    data["trip"]["dates"] = parts[1]
    save_data(data)
    await update.message.reply_text(
        f"✅ Updated trip:\n*{parts[0]}*\n_{parts[1]}_",
        parse_mode="Markdown"
    )

# ── ADMIN: /addadmin ──────────────────────────────────────────────────────────
async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("⛔ Admin only.")
        return
    if not context.args:
        your_id = update.effective_user.id
        await update.message.reply_text(
            f"Your Telegram user ID: `{your_id}`\n\n"
            "Usage: `/addadmin USER_ID`\n"
            "To add yourself: `/addadmin {your_id}`",
            parse_mode="Markdown"
        )
        return
    try:
        uid = int(context.args[0])
        if uid not in data["admins"]:
            data["admins"].append(uid)
            save_data(data)
        await update.message.reply_text(f"✅ Added admin: `{uid}`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("Invalid user ID. Must be a number.")

# ── /myid helper ─────────────────────────────────────────────────────────────
async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    await update.message.reply_text(
        f"Your Telegram user ID: `{uid}`\n\nShare this with the bot admin to get edit access.",
        parse_mode="Markdown"
    )

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # View commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("itinerary", itinerary))
    app.add_handler(CommandHandler("accoms", accoms))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("links", links))
    app.add_handler(CommandHandler("emergency", emergency))
    app.add_handler(CommandHandler("checklist", checklist))
    app.add_handler(CommandHandler("myid", myid))

    # Day shortcuts
    for day_id in ["thu", "fri", "sat", "sun"]:
        app.add_handler(CommandHandler(f"day_{day_id}", day_direct))

    # Admin commands
    app.add_handler(CommandHandler("addaccom", addaccom))
    app.add_handler(CommandHandler("removeaccom", removeaccom))
    app.add_handler(CommandHandler("addweather", addweather))
    app.add_handler(CommandHandler("addlink", addlink))
    app.add_handler(CommandHandler("addstop", addstop))
    app.add_handler(CommandHandler("edittrip", edittrip))
    app.add_handler(CommandHandler("addadmin", addadmin))

    # Callbacks
    app.add_handler(CallbackQueryHandler(day_callback, pattern="^day_"))
    app.add_handler(CallbackQueryHandler(checklist_callback, pattern="^check_"))
    app.add_handler(CallbackQueryHandler(delaccom_callback, pattern="^delaccom_|^cancel$"))

    print("🤖 TripBot is running...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
