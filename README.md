# 🏔 TripBot — Picos de Europa + Valdesquí

A Telegram bot for your trip group. Everyone can view info, admins can edit it anytime.

---

## ⚡ Quick Setup (5 mins)

### Step 1 — Create your Telegram bot

1. Open Telegram, search for **@BotFather**
2. Send `/newbot`
3. Choose a name: e.g. `Picos Trip Bot`
4. Choose a username: e.g. `picos2026_bot` (must end in `_bot`)
5. BotFather gives you a **token** — looks like `7123456789:AAHx...`
6. Copy it, keep it secret

### Step 2 — Deploy on Railway (free, always-on)

1. Go to **railway.app** → sign up with GitHub (free)
2. New Project → Deploy from GitHub repo → upload this folder
   - Or: **New Project → Empty Project → Add Service → GitHub Repo**
3. In your service → **Variables** tab → add:
   ```
   BOT_TOKEN = your_token_from_step_1
   ```
4. Railway auto-detects the `Procfile` and starts the bot
5. Done — bot runs 24/7 for free on Railway's hobby tier

### Step 3 — Add bot to your group

1. Create a Telegram group with your travel friends
2. Add your bot to the group: search `@your_bot_username` → Add to Group
3. In BotFather, run `/setprivacy` → select your bot → Disable (so bot can read commands in groups)
4. Send `/start` in the group

### Step 4 — Set yourself as admin

1. Send `/myid` in the group to get your Telegram user ID
2. Send `/addadmin YOUR_ID`
3. Share `/myid` with any friends who should also be able to edit

---

## 💬 All Commands

### Everyone can use:
| Command | Description |
|---|---|
| `/start` | Welcome message + command overview |
| `/itinerary` | Full itinerary with day buttons |
| `/day_thu` `/day_fri` `/day_sat` `/day_sun` | Jump to specific day |
| `/accoms` | All accommodation bookings |
| `/weather` | Weather forecast links |
| `/links` | Trail status + key links |
| `/emergency` | Emergency phone numbers |
| `/checklist` | Packing checklist by category |
| `/myid` | Get your Telegram user ID |
| `/help` | Full command reference |

### Admin only (edit commands):
| Command | Example |
|---|---|
| `/addaccom` | `/addaccom Airbnb Arenas \| https://airbnb.com/rooms/123 \| Fri–Sat \| Checkout 11am` |
| `/removeaccom` | `/removeaccom` (shows buttons) or `/removeaccom 2` |
| `/addweather` | `/addweather Potes forecast \| https://accuweather.com/... \| Fri` |
| `/addlink` | `/addlink Park webcam \| https://... \| trail` |
| `/addstop` | `/addstop fri \| 20:00 \| Dinner at La Sidrería \| Try the cider!` |
| `/edittrip` | `/edittrip Trip Name \| Dates` |
| `/addadmin` | `/addadmin 123456789` |

---

## 🗂 Data Storage

All trip data is stored in `data.json` in the same folder. The file is created automatically on first run with all the Picos de Europa trip info pre-loaded.

To reset to defaults: delete `data.json` and restart the bot.

To back up: just copy `data.json`.

---

## 🔧 Running locally (for testing)

```bash
pip install -r requirements.txt
BOT_TOKEN=your_token python bot.py
```

---

## 📁 Files

```
tripobot/
├── bot.py           # Main bot logic
├── data.json        # Trip data (auto-created)
├── requirements.txt # Python dependencies
├── Procfile         # Railway deployment config
└── README.md        # This file
```
