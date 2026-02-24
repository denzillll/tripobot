"""
TripBot v3 — Telegram Mini App
FastAPI serves: the web app, REST API, and Telegram webhook

Multi-tenant: each Telegram group/user gets its own trip data file.
  data.json              → fallback for local testing (chatId = 'default')
  data/trip_<id>.json   → per-chat data in production
"""
import json, os, logging, shutil, uuid, re
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, MenuButtonWebApp, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

logging.basicConfig(level=logging.INFO)

BOT_TOKEN     = os.environ.get("BOT_TOKEN", "")
_raw_url      = os.environ.get("WEB_APP_URL", "").rstrip("/")
WEB_APP_URL   = _raw_url if _raw_url.startswith("https://") else f"https://{_raw_url}" if _raw_url else ""
MINI_APP_LINK = os.environ.get("MINI_APP_LINK", "")

DATA_DIR    = Path("data")
UPLOADS_DIR = Path("static/uploads")
DATA_DIR.mkdir(exist_ok=True)


# ── Data helpers ──────────────────────────────────────────────────────────────

def _safe_id(chat_id) -> str:
    """Sanitise chat_id to a filesystem-safe string."""
    return re.sub(r"[^a-zA-Z0-9]", "_", str(chat_id))

def data_file(chat_id) -> Path:
    if str(chat_id) == "default":
        return Path("data.json")          # backward-compat for local dev
    return DATA_DIR / f"trip_{_safe_id(chat_id)}.json"

def load_data(chat_id="default") -> dict:
    fpath = data_file(chat_id)
    if fpath.exists():
        with open(fpath) as f:
            return json.load(f)
    d = default_data()
    save_data(chat_id, d)
    return d

def save_data(chat_id, data: dict):
    with open(data_file(chat_id), "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def is_admin(user_id: int, data: dict) -> bool:
    admins = data.get("admins", [])
    return len(admins) == 0 or user_id in admins

def default_data() -> dict:
    """Blank template used when a chat opens the app for the first time."""
    return {
        "trip":           {"name": "New Trip", "dates": ""},
        "days":           [],
        "accoms":         [],
        "weather":        [],
        "links":          [],
        "emergency":      [{"name": "Emergency", "number": "112"}],
        "groupChecklist": [],
        "groupProgress":  {},
        "wxLocations":    [],
        "admins":         []
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
    uid     = update.effective_user.id
    chat_id = update.effective_chat.id if update.effective_chat else "default"
    data    = load_data(chat_id)
    role    = "admin" if is_admin(uid, data) else "viewer"
    await update.message.reply_text(
        f"Your ID: `{uid}` ({role})\nChat ID: `{chat_id}`",
        parse_mode="Markdown"
    )

async def cmd_addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id if update.effective_chat else "default"
    data    = load_data(chat_id)
    if not is_admin(update.effective_user.id, data):
        await update.message.reply_text("Not an admin.")
        return
    if not context.args:
        await update.message.reply_text(
            f"Usage: /addadmin USER_ID\n\nYour ID: `{update.effective_user.id}`",
            parse_mode="Markdown"
        )
        return
    try:
        new_id = int(context.args[0])
        if new_id not in data["admins"]:
            data["admins"].append(new_id)
            save_data(chat_id, data)
        await update.message.reply_text(f"Added admin: `{new_id}`", parse_mode="Markdown")
    except ValueError:
        await update.message.reply_text("Invalid ID.")

async def error_handler(_update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Telegram error: {context.error}", exc_info=context.error)

ptb_app.add_handler(CommandHandler("start", cmd_start))
ptb_app.add_handler(CommandHandler("trip",  cmd_start))
ptb_app.add_handler(CommandHandler("myid",  cmd_myid))
ptb_app.add_handler(CommandHandler("addadmin", cmd_addadmin))
ptb_app.add_error_handler(error_handler)


# ── FastAPI App ───────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    if BOT_TOKEN and WEB_APP_URL:
        await ptb_app.bot.set_webhook(f"{WEB_APP_URL}/webhook")
        await ptb_app.initialize()
        await ptb_app.start()
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
    body   = await request.json()
    update = Update.de_json(body, ptb_app.bot)
    await ptb_app.process_update(update)
    return {"ok": True}

@app.get("/")
async def serve_app():
    return FileResponse("static/index.html")

# Trip data — all endpoints accept chat_id query param
@app.get("/api/data")
async def api_get_data(chat_id: str = "default"):
    return load_data(chat_id)

@app.post("/api/data")
async def api_save_data(request: Request, chat_id: str = "default"):
    body = await request.json()
    if "trip" not in body or "days" not in body:
        return JSONResponse({"error": "invalid"}, status_code=400)
    save_data(chat_id, body)
    return {"ok": True}

@app.get("/api/is_admin")
async def api_is_admin(user_id: int, chat_id: str = "default"):
    data = load_data(chat_id)
    return {"is_admin": is_admin(user_id, data)}

@app.post("/api/addadmin")
async def api_add_admin(request: Request):
    body         = await request.json()
    requester_id = body.get("requester_id")
    new_id       = body.get("user_id")
    chat_id      = body.get("chat_id", "default")
    data         = load_data(chat_id)
    if not is_admin(requester_id, data):
        return JSONResponse({"error": "not admin"}, status_code=403)
    if new_id not in data["admins"]:
        data["admins"].append(new_id)
        save_data(chat_id, data)
    return {"ok": True}

# File uploads — stored under static/uploads/<chat_id>_<uuid>.<ext>
@app.post("/api/upload")
async def api_upload(file: UploadFile, chat_id: str = "default"):
    UPLOADS_DIR.mkdir(exist_ok=True)
    ext   = Path(file.filename or "file").suffix.lower()
    fname = f"{_safe_id(chat_id)}_{uuid.uuid4().hex[:10]}{ext}"
    dest  = UPLOADS_DIR / fname
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"url": f"/static/uploads/{fname}", "originalName": file.filename}

# Serve static assets (uploaded files, etc.)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Dev server entry point ────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), reload=False)
