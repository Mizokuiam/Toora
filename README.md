# Toora — Your AI Executive Assistant

Hey there! 👋 Toora is a friendly AI assistant that helps small business owners stay on top of their inbox, meetings, and tasks. Think of it as a smart helper that reads your emails, gives you daily briefings, and even takes action on your behalf (with your approval, of course).

**Try it live:** [https://frontend-production-8833b.up.railway.app](https://frontend-production-8833b.up.railway.app)

Connect your Gmail and Telegram, and you're good to go. No credit card, no fuss.

---

## What can Toora do?

- **Read & summarize your inbox** — Get daily briefings without opening every email
- **Send emails** — Draft replies and send them (you approve first)
- **Search the web** — Research topics, find articles, pull key insights
- **Create Notion tasks** — Turn action items into tasks automatically
- **Log to HubSpot** — Keep your CRM updated with new contacts and notes
- **Check your calendar** — See what's coming up and avoid double-booking
- **Chat in Telegram** — Get briefings and approve actions right from your phone

Everything runs through a single dashboard. You stay in control; Toora handles the busywork.

---

## How it works

```
You (Dashboard or Telegram) → Agent runs → Uses tools (Gmail, Calendar, etc.)
                                         ↓
                    Briefing + optional approvals → Back to you
```

The agent is powered by LangGraph and OpenRouter. It decides which tools to use based on your request, then reports back. Sensitive actions (like sending emails) require your approval via the dashboard or Telegram buttons.

---

## Tech stack

- **Frontend:** Next.js 14, React
- **Backend:** FastAPI, PostgreSQL, Redis
- **AI:** LangGraph, LangChain, OpenRouter API
- **Integrations:** Gmail (IMAP/SMTP), Google Calendar, Telegram, Notion, HubSpot
- **Deploy:** Railway (monorepo with 4 services)

---

## Local development

Clone the repo, set up your `.env` (copy from `.env.example`), and you're off.

```bash
# Backend
pip install -r backend/requirements.txt
uvicorn backend.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Worker (consumes agent jobs)
pip install -r worker/requirements.txt
python worker/main.py

# Bot (Telegram webhook)
pip install -r bot/requirements.txt
uvicorn bot.main:app --port 8001
```

Don’t forget to run migrations:

```bash
alembic upgrade head
```

---

## Environment variables

Copy `.env.example` to `.env` and fill in your values. Key ones:

| Variable | What it's for |
|----------|----------------|
| `DATABASE_URL` | PostgreSQL connection |
| `REDIS_URL` | For job queue and real-time updates |
| `ENCRYPTION_KEY` | Keeps credentials safe (generate with `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`) |

**OpenRouter** (powers the AI): set in **Connections** on the dashboard, not as an env var.

Full list is in `.env.example`.

---

## Deploying to Railway

1. Connect your GitHub repo to Railway
2. Add the environment variables per service
3. Run `alembic upgrade head` once
4. For Telegram: connect in the dashboard, then click **Register Webhook**

That’s it. Railway will handle the rest.

---

## Agent tools

| Tool | What it does | Needs approval? |
|------|--------------|-----------------|
| `read_gmail` | Read unread emails | No |
| `send_email` | Send email via Gmail | Always |
| `read_calendar` | Fetch upcoming events | No |
| `create_calendar_event` | Add an event | Configurable |
| `search_web` | DuckDuckGo search | No |
| `read_webpage` | Extract text from URL | No |
| `create_notion_task` | Create Notion page | Configurable |
| `log_to_hubspot` | Update contact + note | Configurable |
| `send_telegram_message` | Send you a message | No |

---

## License

MIT. Use it, tweak it, make it yours.
