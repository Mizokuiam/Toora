# Toora — Local setup and Telegram webhook

## 1. Environment variables

Create a `.env` file in the project root (copy from `.env.example`). **Never commit `.env`.**

| Variable | Required | How to get |
|----------|----------|------------|
| **OPENROUTER_API_KEY** | Yes (for agent) | [OpenRouter](https://openrouter.ai/) → Keys → Create. Used for DeepSeek model. |
| **DATABASE_URL** | Yes | PostgreSQL connection string. Local: `postgresql://user:password@localhost:5432/toora`. Or create a free DB on [Railway](https://railway.app) → PostgreSQL → copy URL. |
| **REDIS_URL** | Yes (for queue + approvals) | Redis connection string. Local: `redis://localhost:6379/0`. Or Railway → Redis → copy URL. |
| **ENCRYPTION_KEY** | Yes | Generate once (Fernet key): run below and paste into `.env`. |

Generate encryption key (run in project root):

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Paste the output into `.env` as:

```
ENCRYPTION_KEY=<paste_here>
```

**Telegram bot token and Chat ID** are **not** in `.env`. You add them in the dashboard: **Connections** page → Telegram card → paste Bot Token and Chat ID → Save. They are stored encrypted in the database.

- **Bot token:** From [@BotFather](https://t.me/BotFather) → `/newbot` → copy token (e.g. `123456:ABC-DEF...`).
- **Chat ID:** Message [@userinfobot](https://t.me/userinfobot) → it replies with your numeric Chat ID.

---

## 2. Install dependencies and run locally

From project root, using PowerShell:

```powershell
# Create and activate venv (if not already)
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install
pip install -r requirements.txt

# Create DB tables (run once)
python -c "from db.connection import init_db; init_db()"
```

Then run **three** processes (use 3 terminals):

**Terminal 1 — Dashboard**

```powershell
.venv\Scripts\Activate.ps1
streamlit run dashboard/app.py
```

Open http://localhost:8501 → go to **Connections** → add Gmail (optional), **Telegram** (Bot Token + Chat ID), HubSpot, Notion → Save.

**Terminal 2 — Telegram webhook (bot)**

```powershell
.venv\Scripts\Activate.ps1
uvicorn bot.webhook:app --reload --port 8000
```

**Terminal 3 — Agent worker**

```powershell
.venv\Scripts\Activate.ps1
python -m worker.run
```

---

## 3. Telegram webhook setup

The webhook tells Telegram where to send updates (e.g. when the user taps Approve/Reject). You need a **public HTTPS URL** that points to your bot server.

### Option A — Local testing with ngrok

1. Install [ngrok](https://ngrok.com/download) and start a tunnel to your bot:
   ```powershell
   ngrok http 8000
   ```
2. Copy the HTTPS URL (e.g. `https://abc123.ngrok.io`).
3. Set the webhook (replace with your bot token and URL):
   ```powershell
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://abc123.ngrok.io/webhook/telegram"
   ```
   Or in browser:  
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://abc123.ngrok.io/webhook/telegram`

4. Confirm:
   ```powershell
   curl "https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo"
   ```
   You should see `"url":"https://abc123.ngrok.io/webhook/telegram"`.

**Important:** While testing locally, keep **Terminal 2** (uvicorn) and **ngrok** running. If you restart ngrok, the URL changes — set the webhook again with the new URL.

### Option B — Production (Railway)

1. Deploy the bot service on Railway (start command: `uvicorn bot.webhook:app --host 0.0.0.0 --port $PORT`).
2. Copy your Railway app URL (e.g. `https://toora-bot.up.railway.app`).
3. Set webhook:
   ```
   https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://toora-bot.up.railway.app/webhook/telegram
   ```
4. Check:  
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo`

### Remove webhook (e.g. switch to polling or change URL)

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/deleteWebhook
```

---

## 4. Quick test

1. Dashboard: **Connections** → add Telegram (Bot Token + Chat ID) → Save → Test connection.
2. **Home** → “Run Agent Now” (requires Redis + worker running).
3. In Telegram you should get messages from the bot; approval buttons work when the webhook URL is set and the bot server is running.

If the worker or Redis is not running, “Run Agent Now” will show an error; that’s expected until Redis and the worker are up.
