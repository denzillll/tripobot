"""
TripBot v2 — Full button-driven UI with inline edit flows
"""

import json
import os
import logging
from pathlib import Path
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, ConversationHandler, MessageHandler, filters
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
DATA_FILE = Path("data.json")

# Conversation states
(
    ADD_ACCOM_NAME, ADD_ACCOM_URL, ADD_ACCOM_DAY, ADD_ACCOM_NOTES,
    ADD_WEATHER_NAME, ADD_WEATHER_URL, ADD_WEATHER_DAY,
    ADD_STOP_DAY, ADD_STOP_TIME, ADD_STOP_NAME, ADD_STOP_NOTE,
    ADD_LINK_NAME, ADD_LINK_URL, ADD_LINK_CAT,
    EDIT_TRIP_NAME, EDIT_TRIP_DATES,
) = range(16)


# ── Data ──────────────────────────────────────────────────────────────────────

def load_data() -> dict:
    if DATA_FILE.exists():
        with open(DATA_FILE) as f:
            return json.load(f)
    d = default_data()
    save_data(d)
    return d

def save_data(data: dict):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_admin(user_id: int, data: dict) -> bool:
    return len(data.get("admins", [])) == 0 or user_id in data["admins"]

def default_data() -> dict:
    return {
        "trip": {
            "name": "Picos de Europa + Valdesqui",
            "dates": "26 Feb - 1 Mar 2026"
        },
        "days": [
            {
                "id": "thu", "label": "Thu 26 Feb", "title": "Madrid to Burgos", "emoji": "🚗",
                "stops": [
                    {"time": "20:00", "name": "Leave Madrid", "note": "Pick up rental car, fill up fuel, head north on A-1 (~3hrs)"},
                    {"time": "23:00", "name": "Burgos overnight stop", "note": "Sleep here, continue to Picos at 7am Friday"}
                ]
            },
            {
                "id": "fri", "label": "Fri 27 Feb", "title": "Arrive Picos + Ruta del Cares", "emoji": "🥾",
                "stops": [
                    {"time": "07:00", "name": "Drive Burgos to Arenas de Cabrales", "note": "~3hrs via A-67 and AS-114"},
                    {"time": "10:30", "name": "Ruta del Cares", "note": "Poncebos to Cain and back, 24km, 6-7hrs. Bring 2L+ water."},
                    {"time": "17:30", "name": "Back to accommodation", "note": "Rest, dinner in Arenas"}
                ]
            },
            {
                "id": "sat", "label": "Sat 28 Feb", "title": "Lagos de Covadonga", "emoji": "🏔",
                "stops": [
                    {"time": "08:30", "name": "Drive to Lagos de Covadonga", "note": "~30min from Arenas"},
                    {"time": "09:00", "name": "Los Lagos Circuit", "note": "6km easy loop, 2-2.5hrs"},
                    {"time": "12:00", "name": "Lunch in Cangas de Onis", "note": "Good restaurants, 20min from lakes"},
                    {"time": "14:00", "name": "Back at accom - REST", "note": "Sleep early! Alarm 3:45AM. Pack tonight."}
                ]
            },
            {
                "id": "sun", "label": "Sun 1 Mar", "title": "Valdesqui + Drive Home", "emoji": "⛷️",
                "stops": [
                    {"time": "04:00", "name": "Drive Picos to Valdesqui", "note": "~4h15, share driving"},
                    {"time": "09:00", "name": "Valdesqui snowboarding", "note": "Opens 9AM. Buy forfait online in advance!"},
                    {"time": "17:00", "name": "Drive back to Madrid", "note": "1h10. Return car by 23:30."}
                ]
            }
        ],
        "accoms": [],
        "weather": [
            {"name": "Picos de Europa", "url": "https://www.accuweather.com/en/es/picos-de-europa/94802_poi/weather-forecast/94802_poi", "day": "Fri-Sat"},
            {"name": "Arenas de Cabrales (detailed)", "url": "https://www.meteoblue.com/en/weather/week/las-arenas-de-cabrales_spain_3119030", "day": "Fri-Sat"},
            {"name": "Burgos", "url": "https://www.accuweather.com/en/es/burgos/305514/daily-weather-forecast/305514", "day": "Thu"},
            {"name": "Valdesqui snow report", "url": "https://www.valdesqui.es/en/snow-report/", "day": "Sun"}
        ],
        "links": [
            {"name": "Park Trail Status (EN)", "url": "https://parquenacionalpicoseuropa.es/english/plan-your-visit/", "cat": "trail"},
            {"name": "AEMET Mountain Forecast", "url": "https://www.aemet.es/en/eltiempo/prediccion/montana", "cat": "trail"},
            {"name": "Ruta del Cares AllTrails", "url": "https://www.alltrails.com/trail/spain/asturias/pr-pnpe-3-ruta-del-cares--2", "cat": "trail"},
            {"name": "Valdesqui Forfait", "url": "https://www.valdesqui.es", "cat": "booking"}
        ],
        "emergency": [
            {"name": "Spain Emergency", "number": "112"},
            {"name": "Asturias Mountain Rescue", "number": "985 848 614"},
            {"name": "Cantabria Mountain Rescue", "number": "942 748 555"},
            {"name": "Civil Guard", "number": "062"}
        ],
        "checklist": {
            "hiking": ["Ankle-support hiking boots", "2L+ water (no refills on Cares)", "Packed lunch + snacks", "Waterproof jacket", "Warm mid-layer", "Beanie + buff", "Sunscreen + sunglasses", "Offline maps downloaded", "First aid + blister kit"],
            "snowboard": ["Board or skis", "Helmet", "Goggles", "Gloves", "Ski jacket + pants", "Thermal base layers", "Ski socks x2", "Forfait booked online"],
            "admin": ["Rental car confirmed", "All accoms booked", "Cash for rural areas", "Spain SIM / roaming on", "Fuel up before leaving Madrid"]
        },
        "admins": []
    }


# ── Keyboards ─────────────────────────────────────────────────────────────────

def main_menu_kb(is_adm: bool) -> InlineKeyboardMarkup:
    rows = [
        [InlineKeyboardButton("📋 Itinerary", callback_data="m:itinerary"),
         InlineKeyboardButton("🏨 Accommodation", callback_data="m:accoms")],
        [InlineKeyboardButton("🌤 Weather", callback_data="m:weather"),
         InlineKeyboardButton("🔗 Links", callback_data="m:links")],
        [InlineKeyboardButton("🚨 Emergency", callback_data="m:emergency"),
         InlineKeyboardButton("✅ Checklist", callback_data="m:checklist")],
    ]
    if is_adm:
        rows.append([InlineKeyboardButton("⚙️ Edit Trip Info", callback_data="m:edit_trip")])
    return InlineKeyboardMarkup(rows)

def back_kb(dest: str = "main") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("← Back", callback_data=f"m:{dest}")]])

def back_and_add_kb(section: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(f"➕ Add", callback_data=f"add:{section}"),
         InlineKeyboardButton("← Back", callback_data="m:main")]
    ])


# ── Helpers ───────────────────────────────────────────────────────────────────

async def send_or_edit(update: Update, text: str, keyboard: InlineKeyboardMarkup, parse_mode="Markdown"):
    """Edit existing message if callback, else send new."""
    if update.callback_query:
        try:
            await update.callback_query.edit_message_text(text, reply_markup=keyboard, parse_mode=parse_mode, disable_web_page_preview=True)
        except Exception:
            await update.callback_query.message.reply_text(text, reply_markup=keyboard, parse_mode=parse_mode, disable_web_page_preview=True)
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode=parse_mode, disable_web_page_preview=True)


# ── Main Menu ─────────────────────────────────────────────────────────────────

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, edit=False):
    data = load_data()
    adm = is_admin(update.effective_user.id, data)
    text = f"🏔 *{data['trip']['name']}*\n📅 {data['trip']['dates']}\n\nWhat do you want to see?"
    kb = main_menu_kb(adm)
    if edit and update.callback_query:
        await update.callback_query.edit_message_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        msg = update.message or update.callback_query.message
        await msg.reply_text(text, reply_markup=kb, parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)

async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_main_menu(update, context)


# ── Section: Itinerary ────────────────────────────────────────────────────────

async def show_itinerary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    adm = is_admin(update.effective_user.id, data)
    rows = []
    for day in data["days"]:
        rows.append([InlineKeyboardButton(
            f"{day['emoji']} {day['label']} — {day['title']}",
            callback_data=f"day:{day['id']}"
        )])
    if adm:
        rows.append([InlineKeyboardButton("➕ Add stop to a day", callback_data="add:stop")])
    rows.append([InlineKeyboardButton("← Back", callback_data="m:main")])
    await send_or_edit(update, "📋 *Itinerary*\n\nTap a day to see details:", InlineKeyboardMarkup(rows))

async def show_day(update: Update, context: ContextTypes.DEFAULT_TYPE, day_id: str):
    data = load_data()
    day = next((d for d in data["days"] if d["id"] == day_id), None)
    if not day:
        await update.callback_query.answer("Day not found")
        return
    lines = [f"{day['emoji']} *{day['label']} — {day['title']}*\n"]
    for stop in day["stops"]:
        lines.append(f"⏰ `{stop['time']}` *{stop['name']}*")
        if stop.get("note"):
            lines.append(f"_{stop['note']}_")
        lines.append("")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("← Itinerary", callback_data="m:itinerary")]])
    await send_or_edit(update, "\n".join(lines), kb)


# ── Section: Accommodation ────────────────────────────────────────────────────

async def show_accoms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    adm = is_admin(update.effective_user.id, data)
    lines = ["🏨 *Accommodation*\n"]
    if not data["accoms"]:
        lines.append("_No bookings added yet._\n\nTap Add to add your first booking.")
    else:
        for i, a in enumerate(data["accoms"]):
            lines.append(f"*{i+1}. {a['name']}*")
            if a.get("day"):
                lines.append(f"📅 {a['day']}")
            lines.append(f"🔗 [Open booking]({a['url']})")
            if a.get("notes"):
                lines.append(f"_{a['notes']}_")
            lines.append("")

    rows = []
    if adm:
        rows.append([InlineKeyboardButton("➕ Add booking", callback_data="add:accom")])
        if data["accoms"]:
            rows.append([InlineKeyboardButton("🗑 Remove booking", callback_data="del:accom")])
    rows.append([InlineKeyboardButton("← Back", callback_data="m:main")])
    await send_or_edit(update, "\n".join(lines), InlineKeyboardMarkup(rows))

async def show_remove_accom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rows = []
    for i, a in enumerate(data["accoms"]):
        rows.append([InlineKeyboardButton(
            f"🗑 {a['name']} ({a.get('day', '')})",
            callback_data=f"delidx:accom:{i}"
        )])
    rows.append([InlineKeyboardButton("← Back", callback_data="m:accoms")])
    await send_or_edit(update, "Which booking to remove?", InlineKeyboardMarkup(rows))


# ── Section: Weather ──────────────────────────────────────────────────────────

async def show_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    adm = is_admin(update.effective_user.id, data)
    lines = ["🌤 *Weather Forecasts*\n", "_Check these the morning of each hike_\n"]
    for w in data["weather"]:
        day_str = f" ({w['day']})" if w.get("day") else ""
        lines.append(f"• [{w['name']}]({w['url']}){day_str}")

    rows = []
    if adm:
        rows.append([InlineKeyboardButton("➕ Add forecast link", callback_data="add:weather")])
        if data["weather"]:
            rows.append([InlineKeyboardButton("🗑 Remove", callback_data="del:weather")])
    rows.append([InlineKeyboardButton("← Back", callback_data="m:main")])
    await send_or_edit(update, "\n".join(lines), InlineKeyboardMarkup(rows))

async def show_remove_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rows = []
    for i, w in enumerate(data["weather"]):
        rows.append([InlineKeyboardButton(f"🗑 {w['name']}", callback_data=f"delidx:weather:{i}")])
    rows.append([InlineKeyboardButton("← Back", callback_data="m:weather")])
    await send_or_edit(update, "Which forecast to remove?", InlineKeyboardMarkup(rows))


# ── Section: Links ────────────────────────────────────────────────────────────

async def show_links(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    adm = is_admin(update.effective_user.id, data)
    trail = [l for l in data["links"] if l.get("cat") == "trail"]
    booking = [l for l in data["links"] if l.get("cat") == "booking"]
    other = [l for l in data["links"] if l.get("cat") not in ("trail", "booking")]

    lines = ["🔗 *Key Links*\n"]
    if trail:
        lines.append("*Trail Status:*")
        for l in trail:
            lines.append(f"• [{l['name']}]({l['url']})")
        lines.append("")
    if booking:
        lines.append("*Bookings:*")
        for l in booking:
            lines.append(f"• [{l['name']}]({l['url']})")
        lines.append("")
    if other:
        lines.append("*Other:*")
        for l in other:
            lines.append(f"• [{l['name']}]({l['url']})")

    rows = []
    if adm:
        rows.append([InlineKeyboardButton("➕ Add link", callback_data="add:link")])
        if data["links"]:
            rows.append([InlineKeyboardButton("🗑 Remove", callback_data="del:link")])
    rows.append([InlineKeyboardButton("← Back", callback_data="m:main")])
    await send_or_edit(update, "\n".join(lines), InlineKeyboardMarkup(rows))

async def show_remove_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    rows = []
    for i, l in enumerate(data["links"]):
        rows.append([InlineKeyboardButton(f"🗑 {l['name']}", callback_data=f"delidx:link:{i}")])
    rows.append([InlineKeyboardButton("← Back", callback_data="m:links")])
    await send_or_edit(update, "Which link to remove?", InlineKeyboardMarkup(rows))


# ── Section: Emergency ────────────────────────────────────────────────────────

async def show_emergency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    lines = ["🚨 *Emergency Numbers*\n"]
    for e in data["emergency"]:
        lines.append(f"*{e['name']}*\n`{e['number']}`\n")
    lines.append("_In any emergency in Spain: call *112* first_")
    await send_or_edit(update, "\n".join(lines), back_kb("main"))


# ── Section: Checklist ────────────────────────────────────────────────────────

async def show_checklist_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🥾 Hiking Gear", callback_data="cl:hiking")],
        [InlineKeyboardButton("⛷️ Snowboard Gear", callback_data="cl:snowboard")],
        [InlineKeyboardButton("🚗 Trip Admin", callback_data="cl:admin")],
        [InlineKeyboardButton("← Back", callback_data="m:main")]
    ])
    await send_or_edit(update, "✅ *Packing Checklist*\n\nChoose a category:", kb)

async def show_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE, cat: str):
    data = load_data()
    items = data["checklist"].get(cat, [])
    labels = {"hiking": "🥾 Hiking Gear", "snowboard": "⛷️ Snowboard Gear", "admin": "🚗 Trip Admin"}
    lines = [f"*{labels.get(cat, cat)}*\n"]
    for item in items:
        lines.append(f"☐  {item}")
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("← Back", callback_data="m:checklist")]])
    await send_or_edit(update, "\n".join(lines), kb)


# ── Section: Edit Trip Info ───────────────────────────────────────────────────

async def show_edit_trip(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    text = (
        f"⚙️ *Edit Trip Info*\n\n"
        f"Name: _{data['trip']['name']}_\n"
        f"Dates: _{data['trip']['dates']}_\n\n"
        "What would you like to change?"
    )
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("✏️ Trip name", callback_data="edit:trip_name"),
         InlineKeyboardButton("✏️ Dates", callback_data="edit:trip_dates")],
        [InlineKeyboardButton("👤 My user ID", callback_data="edit:myid")],
        [InlineKeyboardButton("← Back", callback_data="m:main")]
    ])
    await send_or_edit(update, text, kb)


# ── Master callback router ────────────────────────────────────────────────────

async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    d = query.data

    # Navigation
    if d == "m:main":
        await show_main_menu(update, context, edit=True)
    elif d == "m:itinerary":
        await show_itinerary(update, context)
    elif d == "m:accoms":
        await show_accoms(update, context)
    elif d == "m:weather":
        await show_weather(update, context)
    elif d == "m:links":
        await show_links(update, context)
    elif d == "m:emergency":
        await show_emergency(update, context)
    elif d == "m:checklist":
        await show_checklist_menu(update, context)
    elif d == "m:edit_trip":
        await show_edit_trip(update, context)

    # Day detail
    elif d.startswith("day:"):
        await show_day(update, context, d.split(":")[1])

    # Checklist category
    elif d.startswith("cl:"):
        await show_checklist(update, context, d.split(":")[1])

    # Delete screens
    elif d == "del:accom":
        await show_remove_accom(update, context)
    elif d == "del:weather":
        await show_remove_weather(update, context)
    elif d == "del:link":
        await show_remove_link(update, context)

    # Actual deletion
    elif d.startswith("delidx:"):
        _, section, idx = d.split(":")
        idx = int(idx)
        data = load_data()
        if not is_admin(query.from_user.id, data):
            await query.answer("Admin only", show_alert=True)
            return
        key_map = {"accom": "accoms", "weather": "weather", "link": "links"}
        key = key_map.get(section)
        if key and 0 <= idx < len(data[key]):
            removed = data[key].pop(idx)
            save_data(data)
            await query.answer(f"Removed: {removed.get('name', 'item')}")
        back_map = {"accom": "m:accoms", "weather": "m:weather", "link": "m:links"}
        query.data = back_map.get(section, "m:main")
        await router(update, context)

    # Edit trip inline
    elif d == "edit:myid":
        uid = query.from_user.id
        await query.answer(f"Your ID: {uid}", show_alert=True)

    # Add flows — these start ConversationHandlers, handled below
    # (just answer and let the conv handler catch the next message)


# ── Conversation: Add Accommodation ──────────────────────────────────────────

async def add_accom_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    if not is_admin(query.from_user.id, data):
        await query.answer("Admin only", show_alert=True)
        return ConversationHandler.END
    context.user_data.clear()
    await query.edit_message_text(
        "🏨 *Add Accommodation*\n\nStep 1 of 4\n\nWhat's the name of the place?\n_(e.g. Airbnb Arenas, Hotel Rural Picos)_\n\n/cancel to go back",
        parse_mode="Markdown"
    )
    return ADD_ACCOM_NAME

async def add_accom_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["accom_name"] = update.message.text
    await update.message.reply_text(
        f"Got it: _{update.message.text}_\n\nStep 2 of 4\n\nPaste the booking URL:\n_(Airbnb, Booking.com, etc.)_",
        parse_mode="Markdown"
    )
    return ADD_ACCOM_URL

async def add_accom_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["accom_url"] = update.message.text
    await update.message.reply_text(
        "Step 3 of 4\n\nWhich nights? _(e.g. Thu, Fri-Sat, All nights)_\n\nOr tap /skip",
        parse_mode="Markdown"
    )
    return ADD_ACCOM_DAY

async def add_accom_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["accom_day"] = update.message.text
    await update.message.reply_text(
        "Step 4 of 4\n\nAny notes? _(e.g. Checkout 11am, Free parking, Contact: +34...)_\n\nOr tap /skip",
        parse_mode="Markdown"
    )
    return ADD_ACCOM_NOTES

async def add_accom_skip_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["accom_day"] = ""
    await update.message.reply_text(
        "Step 4 of 4\n\nAny notes? _(e.g. Checkout 11am, Free parking)_\n\nOr tap /skip",
        parse_mode="Markdown"
    )
    return ADD_ACCOM_NOTES

async def add_accom_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["accom_notes"] = update.message.text
    return await _save_accom(update, context)

async def add_accom_skip_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["accom_notes"] = ""
    return await _save_accom(update, context)

async def _save_accom(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    accom = {
        "name": context.user_data.get("accom_name", ""),
        "url": context.user_data.get("accom_url", ""),
        "day": context.user_data.get("accom_day", ""),
        "notes": context.user_data.get("accom_notes", "")
    }
    data["accoms"].append(accom)
    save_data(data)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🏨 View Accommodations", callback_data="m:accoms")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="m:main")]
    ])
    await update.message.reply_text(
        f"Added!\n\n*{accom['name']}*\n"
        f"📅 {accom['day'] or 'Nights not specified'}\n"
        f"🔗 {accom['url']}\n"
        f"{'_' + accom['notes'] + '_' if accom['notes'] else ''}",
        reply_markup=kb, parse_mode="Markdown"
    )
    context.user_data.clear()
    return ConversationHandler.END


# ── Conversation: Add Weather Link ────────────────────────────────────────────

async def add_weather_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    if not is_admin(query.from_user.id, data):
        await query.answer("Admin only", show_alert=True)
        return ConversationHandler.END
    context.user_data.clear()
    await query.edit_message_text(
        "🌤 *Add Weather Link*\n\nStep 1 of 3\n\nName for this forecast?\n_(e.g. Potes hourly, Covadonga)_\n\n/cancel to go back",
        parse_mode="Markdown"
    )
    return ADD_WEATHER_NAME

async def add_weather_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["w_name"] = update.message.text
    await update.message.reply_text("Step 2 of 3\n\nPaste the forecast URL:")
    return ADD_WEATHER_URL

async def add_weather_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["w_url"] = update.message.text
    await update.message.reply_text(
        "Step 3 of 3\n\nWhich day is this for? _(e.g. Fri-Sat, Sunday)_\n\nOr /skip"
    )
    return ADD_WEATHER_DAY

async def add_weather_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["w_day"] = update.message.text
    return await _save_weather(update, context)

async def add_weather_skip_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["w_day"] = ""
    return await _save_weather(update, context)

async def _save_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    entry = {
        "name": context.user_data.get("w_name", ""),
        "url": context.user_data.get("w_url", ""),
        "day": context.user_data.get("w_day", "")
    }
    data["weather"].append(entry)
    save_data(data)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🌤 View Weather", callback_data="m:weather")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="m:main")]
    ])
    await update.message.reply_text(
        f"Added: *{entry['name']}*", reply_markup=kb, parse_mode="Markdown"
    )
    context.user_data.clear()
    return ConversationHandler.END


# ── Conversation: Add Link ────────────────────────────────────────────────────

async def add_link_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    if not is_admin(query.from_user.id, data):
        await query.answer("Admin only", show_alert=True)
        return ConversationHandler.END
    context.user_data.clear()
    await query.edit_message_text(
        "🔗 *Add Key Link*\n\nStep 1 of 3\n\nName for this link?\n_(e.g. Park webcam, Cares gorge info)_\n\n/cancel to go back",
        parse_mode="Markdown"
    )
    return ADD_LINK_NAME

async def add_link_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["l_name"] = update.message.text
    await update.message.reply_text("Step 2 of 3\n\nPaste the URL:")
    return ADD_LINK_URL

async def add_link_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["l_url"] = update.message.text
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🥾 Trail", callback_data="lcat:trail"),
         InlineKeyboardButton("🎫 Booking", callback_data="lcat:booking"),
         InlineKeyboardButton("📌 Other", callback_data="lcat:other")]
    ])
    await update.message.reply_text("Step 3 of 3\n\nCategory:", reply_markup=kb)
    return ADD_LINK_CAT

async def add_link_cat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    cat = query.data.replace("lcat:", "")
    data = load_data()
    entry = {
        "name": context.user_data.get("l_name", ""),
        "url": context.user_data.get("l_url", ""),
        "cat": cat
    }
    data["links"].append(entry)
    save_data(data)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 View Links", callback_data="m:links")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="m:main")]
    ])
    await query.edit_message_text(
        f"Added: *{entry['name']}* [{cat}]", reply_markup=kb, parse_mode="Markdown"
    )
    context.user_data.clear()
    return ConversationHandler.END


# ── Conversation: Add Itinerary Stop ─────────────────────────────────────────

async def add_stop_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    if not is_admin(query.from_user.id, data):
        await query.answer("Admin only", show_alert=True)
        return ConversationHandler.END
    context.user_data.clear()
    rows = [[InlineKeyboardButton(f"{d['emoji']} {d['label']}", callback_data=f"stopday:{d['id']}")] for d in data["days"]]
    await query.edit_message_text(
        "📋 *Add Itinerary Stop*\n\nWhich day?\n\n/cancel to go back",
        reply_markup=InlineKeyboardMarkup(rows), parse_mode="Markdown"
    )
    return ADD_STOP_DAY

async def add_stop_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["stop_day"] = query.data.replace("stopday:", "")
    await query.edit_message_text("What time? _(e.g. 19:30, ~21:00)_", parse_mode="Markdown")
    return ADD_STOP_TIME

async def add_stop_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stop_time"] = update.message.text
    await update.message.reply_text("Name of the stop? _(e.g. Dinner at La Sidreria)_")
    return ADD_STOP_NAME

async def add_stop_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stop_name"] = update.message.text
    await update.message.reply_text("Any notes? _(e.g. Reserve in advance, try the cider)_\n\nOr /skip")
    return ADD_STOP_NOTE

async def add_stop_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stop_note"] = update.message.text
    return await _save_stop(update, context)

async def add_stop_skip_note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["stop_note"] = ""
    return await _save_stop(update, context)

async def _save_stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    day_id = context.user_data.get("stop_day")
    day = next((d for d in data["days"] if d["id"] == day_id), None)
    if not day:
        await update.message.reply_text("Day not found.")
        return ConversationHandler.END
    stop = {
        "time": context.user_data.get("stop_time", ""),
        "name": context.user_data.get("stop_name", ""),
        "note": context.user_data.get("stop_note", "")
    }
    day["stops"].append(stop)
    save_data(data)
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("📋 View Itinerary", callback_data="m:itinerary")],
        [InlineKeyboardButton("🏠 Main Menu", callback_data="m:main")]
    ])
    await update.message.reply_text(
        f"Added to *{day['label']}*:\n`{stop['time']}` {stop['name']}",
        reply_markup=kb, parse_mode="Markdown"
    )
    context.user_data.clear()
    return ConversationHandler.END


# ── Conversation: Edit Trip Name/Dates ────────────────────────────────────────

async def edit_trip_name_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    if not is_admin(query.from_user.id, data):
        await query.answer("Admin only", show_alert=True)
        return ConversationHandler.END
    await query.edit_message_text(
        f"Current name: _{data['trip']['name']}_\n\nType the new trip name:\n\n/cancel to go back",
        parse_mode="Markdown"
    )
    return EDIT_TRIP_NAME

async def edit_trip_name_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    data["trip"]["name"] = update.message.text
    save_data(data)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("← Back to Edit", callback_data="m:edit_trip")]])
    await update.message.reply_text(f"Updated trip name: *{update.message.text}*", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END

async def edit_trip_dates_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = load_data()
    if not is_admin(query.from_user.id, data):
        await query.answer("Admin only", show_alert=True)
        return ConversationHandler.END
    await query.edit_message_text(
        f"Current dates: _{data['trip']['dates']}_\n\nType the new dates:\n_(e.g. 26 Feb - 1 Mar 2026)_\n\n/cancel to go back",
        parse_mode="Markdown"
    )
    return EDIT_TRIP_DATES

async def edit_trip_dates_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    data["trip"]["dates"] = update.message.text
    save_data(data)
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("← Back to Edit", callback_data="m:edit_trip")]])
    await update.message.reply_text(f"Updated dates: *{update.message.text}*", reply_markup=kb, parse_mode="Markdown")
    return ConversationHandler.END


# ── Cancel (universal) ────────────────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Main Menu", callback_data="m:main")]])
    await update.message.reply_text("Cancelled.", reply_markup=kb)
    return ConversationHandler.END


# ── /myid ─────────────────────────────────────────────────────────────────────

async def myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = load_data()
    adm = is_admin(uid, data)
    status = "You are an admin" if adm else "You are not an admin yet"
    await update.message.reply_text(
        f"Your Telegram user ID: `{uid}`\n_{status}_",
        parse_mode="Markdown"
    )


# ── /addadmin ─────────────────────────────────────────────────────────────────

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("Admin only.")
        return
    if not context.args:
        await update.message.reply_text(
            f"Your ID: `{update.effective_user.id}`\n\nUsage: `/addadmin USER_ID`",
            parse_mode="Markdown"
        )
        return
    try:
        new_id = int(context.args[0])
        if new_id not in data["admins"]:
            data["admins"].append(new_id)
            save_data(data)
        await update.message.reply_text(f"Added admin: `{new_id}`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("Invalid ID — must be a number. Use /myid to get yours.")


# ── Main ──────────────────────────────────────────────────────────────────────

def make_conv(entry_point_data: str, states: dict, name: str) -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(states[entry_point_data], pattern=f"^add:{entry_point_data}$")
                      if not entry_point_data.startswith("edit:") else
                      CallbackQueryHandler(states[entry_point_data], pattern=f"^{entry_point_data}$")],
        states=states,
        fallbacks=[CommandHandler("cancel", cancel)],
        name=name,
        per_message=False
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Conversation: Add accommodation
    accom_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_accom_start, pattern="^add:accom$")],
        states={
            ADD_ACCOM_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_accom_name)],
            ADD_ACCOM_URL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_accom_url)],
            ADD_ACCOM_DAY:  [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_accom_day),
                CommandHandler("skip", add_accom_skip_day)
            ],
            ADD_ACCOM_NOTES: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_accom_notes),
                CommandHandler("skip", add_accom_skip_notes)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Conversation: Add weather
    weather_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_weather_start, pattern="^add:weather$")],
        states={
            ADD_WEATHER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_weather_name)],
            ADD_WEATHER_URL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_weather_url)],
            ADD_WEATHER_DAY:  [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_weather_day),
                CommandHandler("skip", add_weather_skip_day)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Conversation: Add link
    link_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_link_start, pattern="^add:link$")],
        states={
            ADD_LINK_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_link_name)],
            ADD_LINK_URL:  [MessageHandler(filters.TEXT & ~filters.COMMAND, add_link_url)],
            ADD_LINK_CAT:  [CallbackQueryHandler(add_link_cat, pattern="^lcat:")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Conversation: Add stop
    stop_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_stop_start, pattern="^add:stop$")],
        states={
            ADD_STOP_DAY:  [CallbackQueryHandler(add_stop_day, pattern="^stopday:")],
            ADD_STOP_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_stop_time)],
            ADD_STOP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_stop_name)],
            ADD_STOP_NOTE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_stop_note),
                CommandHandler("skip", add_stop_skip_note)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Conversation: Edit trip name
    edit_name_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_trip_name_start, pattern="^edit:trip_name$")],
        states={
            EDIT_TRIP_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_trip_name_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Conversation: Edit trip dates
    edit_dates_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_trip_dates_start, pattern="^edit:trip_dates$")],
        states={
            EDIT_TRIP_DATES: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_trip_dates_save)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False
    )

    # Add all handlers
    for conv in [accom_conv, weather_conv, link_conv, stop_conv, edit_name_conv, edit_dates_conv]:
        app.add_handler(conv)

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("myid", myid))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.add_handler(CallbackQueryHandler(router))

    print("TripBot v2 running...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()