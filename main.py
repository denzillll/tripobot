"""
TripBot v3 — Telegram Mini App
FastAPI serves: the web app, REST API, and Telegram webhook
"""
import json, os, logging
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN  = os.environ.get("BOT_TOKEN", "")
_raw_url = os.environ.get("WEB_APP_URL", "").rstrip("/")
WEB_APP_URL = _raw_url if _raw_url.startswith("https://") else f"https://{_raw_url}" if _raw_url else ""
MINI_APP_LINK = os.environ.get("MINI_APP_LINK", "")  # e.g. https://t.me/YourBot/AppName
DATA_FILE  = Path("data.json")


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
    admins = data.get("admins", [])
    return len(admins) == 0 or user_id in admins

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
                    {"time": "20:00", "name": "Leave Madrid", "note": "Pick up rental car, fill up fuel, head north on A-1 toward Burgos (~3hrs)"},
                    {"time": "23:00", "name": "Burgos overnight stop", "note": "Sleep here, continue to Picos at 7am Friday"}
                ]
            },
            {
                "id": "fri", "label": "Fri 27 Feb", "title": "Arrive Picos + Ruta del Cares", "emoji": "🥾",
                "stops": [
                    {"time": "07:00", "name": "Drive Burgos to Arenas de Cabrales", "note": "~3hrs via A-67 and AS-114"},
                    {"time": "10:30", "name": "Ruta del Cares", "note": "Poncebos to Cain and back, 24km, 6-7hrs. Rockfall warning active. Bring 2L+ water."},
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
            {"name": "Ruta del Cares on AllTrails", "url": "https://www.alltrails.com/trail/spain/asturias/pr-pnpe-3-ruta-del-cares--2", "cat": "trail"},
            {"name": "Valdesqui Forfait", "url": "https://www.valdesqui.es", "cat": "booking"}
        ],
        "emergency": [
            {"name": "Spain Emergency", "number": "112"},
            {"name": "Asturias Mountain Rescue", "number": "985 848 614"},
            {"name": "Cantabria Mountain Rescue", "number": "942 748 555"},
            {"name": "Civil Guard", "number": "062"}
        ],
        "groupChecklist": [
            {"id": "hiking",    "label": "Hiking Gear",    "icon": "🥾", "items": ["Ankle-support hiking boots", "2L+ water (no refills on Cares)", "Packed lunch + snacks", "Waterproof jacket", "Warm mid-layer", "Beanie + buff", "Sunscreen + sunglasses", "Offline maps downloaded", "First aid + blister kit"]},
            {"id": "snowboard", "label": "Snowboard Gear", "icon": "⛷️", "items": ["Board or skis", "Helmet", "Goggles", "Gloves", "Ski jacket + pants", "Thermal base layers", "Ski socks x2", "Forfait booked online"]},
            {"id": "admin",     "label": "Trip Admin",     "icon": "🚗", "items": ["Rental car confirmed", "All accoms booked", "Cash for rural areas", "Spain SIM / roaming on", "Fuel up before leaving Madrid"]}
        ],
        "groupProgress": {},
        "wxLocations": [
            {"name": "Burgos",          "tag": "Thu 26",     "lat": 42.3439, "lon": -3.6969, "dateFrom": "2026-02-26", "dateTo": "2026-02-26", "wind": False, "snow": False, "forecastUrl": "https://www.accuweather.com/en/es/burgos/305514/daily-weather-forecast/305514",                                          "forecastName": "AccuWeather Burgos"},
            {"name": "Picos de Europa", "tag": "Fri 27\u2013Sat 28", "lat": 43.2520, "lon": -4.8492, "dateFrom": "2026-02-27", "dateTo": "2026-02-28", "wind": True,  "snow": False, "forecastUrl": "https://www.meteoblue.com/en/weather/week/las-arenas-de-cabrales_spain_3119030",                         "forecastName": "Meteoblue Arenas de Cabrales"},
            {"name": "Valdesqui",       "tag": "Sun 1",      "lat": 40.8897, "lon": -3.9153, "dateFrom": "2026-03-01", "dateTo": "2026-03-01", "wind": False, "snow": True,  "forecastUrl": "https://www.valdesqui.es/en/snow-report/",                                                                              "forecastName": "Valdesqui snow report"}
        ],
        "admins": []
    }


# ── Telegram Bot ──────────────────────────────────────────────────────────────

ptb_app = Application.builder().token(BOT_TOKEN).build()

async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    link = MINI_APP_LINK or WEB_APP_URL
    logging.info(f"cmd_start: using link={repr(link)}")
    if not link:
        await update.message.reply_text("WEB_APP_URL not configured.")
        return
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("🏔 Open Trip Planner", url=link)
    ]])
    await update.message.reply_text(
        "Tap below to open the trip planner.",
        reply_markup=kb
    )

async def cmd_myid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    data = load_data()
    role = "admin" if is_admin(uid, data) else "viewer"
    await update.message.reply_text(f"Your ID: `{uid}` ({role})", parse_mode="Markdown")

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("Not an admin.")
        return
    if not context.args:
        await update.message.reply_text(f"Usage: /addadmin USER_ID\n\nYour ID: `{update.effective_user.id}`", parse_mode="Markdown")
        return
    try:
        new_id = int(context.args[0])
        if new_id not in data["admins"]:
            data["admins"].append(new_id)
            save_data(data)
        await update.message.reply_text(f"Added admin: `{new_id}`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("Invalid ID.")

async def error_handler(_update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Telegram error: {context.error}", exc_info=context.error)

ptb_app.add_handler(CommandHandler("start", cmd_start))
ptb_app.add_handler(CommandHandler("trip", cmd_start))
ptb_app.add_handler(CommandHandler("myid", cmd_myid))
ptb_app.add_handler(CommandHandler("addadmin", cmd_addadmin))
ptb_app.add_error_handler(error_handler)


# ── FastAPI App ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    if BOT_TOKEN and WEB_APP_URL:
        await ptb_app.bot.set_webhook(f"{WEB_APP_URL}/webhook")
        await ptb_app.initialize()
        await ptb_app.start()
        # Set the persistent menu button that shows on every chat
        try:
            await ptb_app.bot.set_chat_menu_button(
                menu_button=MenuButtonWebApp(
                    text="🏔 Trip",
                    web_app=WebAppInfo(url=WEB_APP_URL)
                )
            )
        except Exception as e:
            logging.warning(f"Could not set menu button: {e}")
    yield
    if BOT_TOKEN and WEB_APP_URL:
        await ptb_app.stop()
        await ptb_app.shutdown()

app = FastAPI(lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


# ── Routes ────────────────────────────────────────────────────────────────────

@app.post("/webhook")
async def telegram_webhook(request: Request):
    body = await request.json()
    update = Update.de_json(body, ptb_app.bot)
    await ptb_app.process_update(update)
    return {"ok": True}

@app.get("/")
async def serve_app():
    return FileResponse("static/index.html")

@app.get("/api/data")
async def api_get_data():
    return load_data()

@app.post("/api/data")
async def api_save_data(request: Request):
    body = await request.json()
    # Basic validation
    if "trip" not in body or "days" not in body:
        return JSONResponse({"error": "invalid"}, status_code=400)
    save_data(body)
    return {"ok": True}

@app.get("/api/is_admin")
async def api_is_admin(user_id: int):
    data = load_data()
    return {"is_admin": is_admin(user_id, data)}

@app.post("/api/addadmin")
async def api_add_admin(request: Request):
    body = await request.json()
    requester_id = body.get("requester_id")
    new_id = body.get("user_id")
    data = load_data()
    if not is_admin(requester_id, data):
        return JSONResponse({"error": "not admin"}, status_code=403)
    if new_id not in data["admins"]:
        data["admins"].append(new_id)
        save_data(data)
    return {"ok": True}


# ── Dev server entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=False)
