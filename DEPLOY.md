# Toora — Railway deployment

## Project

- **Railway project ID:** `0d70f7fc-374d-40d3-b572-bb291f806939`
- **Project name:** Toora
- **Environment:** production

## Services

| Service | Purpose | Public URL |
|--------|---------|------------|
| **web** | Telegram bot webhook (FastAPI) | https://web-production-8fda4.up.railway.app |
| **worker** | Agent runner (LangGraph, Redis consumer) | No public URL |

## Required: Worker start command

The repo has one `railway.toml` (used by **web**). The **worker** service must use a different start command.

In Railway dashboard:

1. Open project **Toora** → **worker** service.
2. Go to **Settings** → **Deploy** (or **Start Command**).
3. Set **Custom start command** to:
   ```bash
   python -m worker.run
   ```
4. Save. Redeploy the worker if needed.

## Required: Environment variables

Set these for **both** services (or at **project** level so they apply to all services):

| Variable | Description |
|----------|-------------|
| **DATABASE_URL** | PostgreSQL connection string (from Railway Postgres: add Postgres to project → Variables → copy `DATABASE_URL`) |
| **REDIS_URL** | Redis connection string (from Railway Redis: add Redis to project → Variables → copy `REDIS_URL`) |
| **ENCRYPTION_KEY** | Fernet key for encrypting credentials. Generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"` |
| **OPENROUTER_API_KEY** | Your OpenRouter API key (for DeepSeek via agent) |

How to set in Railway:

1. Project **Toora** → **Variables** (project-level), or open each service → **Variables**.
2. Add each variable. If Postgres/Redis are in the same project, `DATABASE_URL` and `REDIS_URL` are often auto-injected when you link those services to **web** and **worker**.

## Telegram webhook

After **web** is deployed and variables are set, register the webhook:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://web-production-8fda4.up.railway.app/webhook/telegram
```

Replace `<YOUR_BOT_TOKEN>` with your bot token. Check:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getWebhookInfo
```

## Health check

- **Web:** https://web-production-8fda4.up.railway.app/health

## Linking this repo to Railway (CLI)

From project root:

```bash
railway link -p 0d70f7fc-374d-40d3-b572-bb291f806939 -e production -s web
# or for worker:
railway link -p 0d70f7fc-374d-40d3-b572-bb291f806939 -e production -s worker
```
