# Toora v2 — AI Executive Assistant

> Production-ready autonomous AI agent for small business owners.  
> Next.js 14 + FastAPI monorepo, deployed on Railway.

**Live:** https://smoort.com &nbsp;|&nbsp; **API:** https://smoort-production.up.railway.app

---

## Architecture

```
Browser → Next.js (frontend) → FastAPI (backend) → PostgreSQL + Redis
                                                 ↕ WebSocket (real-time)
                        Worker (LangGraph agent) ──→ Tools (Gmail, Search, Notion, HubSpot)
                        Bot (Telegram webhook)   ──→ Approval resolution
```

Four Railway services share one PostgreSQL and one Redis instance.

---

## Services

| Service | Directory | Start command |
|---------|-----------|---------------|
| frontend | `frontend/` | `npm run start` |
| backend | `backend/` | `uvicorn backend.main:app --host 0.0.0.0 --port $PORT` |
| worker | `worker/` | `python worker/main.py` |
| bot | `bot/` | `uvicorn bot.main:app --host 0.0.0.0 --port $PORT` |

---

## Environment Variables

Copy `.env.example` → `.env` and fill all values.

| Variable | Used by | Description |
|----------|---------|-------------|
| `OPENROUTER_API_KEY` | worker | LLM access via OpenRouter |
| `DATABASE_URL` | all Python services | PostgreSQL connection string |
| `REDIS_URL` | all Python services | Redis connection string |
| `ENCRYPTION_KEY` | backend, bot, worker | Fernet key for credential encryption |
| `BACKEND_URL` | frontend | FastAPI public URL |
| `FRONTEND_URL` | backend | Next.js public URL (for CORS) |
| `NEXT_PUBLIC_API_URL` | frontend (browser) | Backend URL exposed to browser |
| `TELEGRAM_WEBHOOK_SECRET` | bot | Webhook verification header |

Generate encryption key once:
```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

---

## Database Migrations

Run from repo root with `DATABASE_URL` set:
```bash
alembic upgrade head
```

This creates all 6 tables and seeds the default user + agent config.

---

## Local Development

### Backend
```bash
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload
```

### Frontend
```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

### Worker
```bash
pip install -r worker/requirements.txt
python worker/main.py
```

### Bot
```bash
pip install -r bot/requirements.txt
uvicorn bot.main:app --port 8001
```

---

## Features

- **Dashboard** — Real-time agent status, live activity feed via WebSocket, one-click agent run
- **Connections** — Encrypted credential management for Gmail, Telegram, HubSpot, Notion
- **Agent Config** — System prompt, tool toggles, run schedule, approval rules
- **Action Log** — Paginated, filterable table with full input/output detail
- **Approvals** — Real-time pending approvals, approve/reject from dashboard or Telegram
- **Settings** — Notification preferences, danger zone with confirmation dialogs

## Agent Tools

| Tool | Description | Approval |
|------|-------------|----------|
| `read_gmail` | Read unread emails via IMAP | No |
| `send_email` | Send email via SMTP | Always |
| `search_web` | DuckDuckGo search | No |
| `read_webpage` | Extract article text from URL | No |
| `create_notion_task` | Create Notion database page | Configurable |
| `log_to_hubspot` | Create/update HubSpot contact + note | Configurable |
| `send_telegram_message` | Send Telegram message | No |

---

## Deployment (Railway)

1. Push to `main` branch — Railway auto-deploys all four services.
2. Set all environment variables per service in the Railway dashboard.
3. Run `alembic upgrade head` once via Railway shell or a one-off command.
4. Register the Telegram webhook:
   ```
   https://api.telegram.org/bot{TOKEN}/setWebhook?url=https://{BOT_URL}/webhook/telegram&secret_token={TELEGRAM_WEBHOOK_SECRET}
   ```
