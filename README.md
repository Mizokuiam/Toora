# Toora — AI Executive Assistant for Small Business

An autonomous AI agent that acts as an executive assistant: monitors Gmail, does web research, manages tasks in Notion, logs to HubSpot CRM, and communicates with the user through Telegram before taking consequential actions. Control and monitor everything via a Streamlit dashboard.

## Tech stack

- **Agent:** LangGraph-style ReAct with OpenRouter (DeepSeek)
- **Search:** duckduckgo-search
- **Web reading:** trafilatura
- **Email:** Gmail IMAP/SMTP (App Password)
- **Communication:** Telegram Bot API
- **CRM:** HubSpot Private App
- **Tasks:** Notion API
- **Database:** PostgreSQL (Railway)
- **Queue/cache:** Redis (Railway)
- **Dashboard:** Streamlit (Streamlit Cloud)
- **Credentials:** Encrypted in PostgreSQL (Fernet), key from env

## Architecture

- **Streamlit app** — Dashboard + admin (Streamlit Cloud). Pushes jobs to Redis.
- **Agent worker** — Python process on Railway; consumes Redis queue, runs LangGraph agent.
- **Telegram bot** — FastAPI webhook on Railway; receives Approve/Reject callbacks.

## Setup

1. Clone and create virtualenv:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   pip install -r requirements.txt
   ```

2. Copy `.env.example` to `.env` and set:
   - `OPENROUTER_API_KEY`
   - `DATABASE_URL` (PostgreSQL)
   - `REDIS_URL`
   - `ENCRYPTION_KEY` (generate: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)

3. Run migrations (dashboard or worker):
   ```bash
   python -c "from db.connection import init_db; init_db()"
   ```

4. **Dashboard (Streamlit):**
   ```bash
   streamlit run dashboard/app.py
   ```
   Or point Streamlit Cloud to `dashboard/app.py`.

5. **Telegram bot (Railway):** Deploy with start command:
   ```bash
   uvicorn bot.webhook:app --host 0.0.0.0 --port $PORT
   ```
   Set Telegram webhook URL to `https://your-railway-app.up.railway.app/webhook/telegram`.

6. **Worker (Railway):** Deploy as second service with:
   ```bash
   python -m worker.run
   ```

## Project layout

- `dashboard/` — Streamlit pages (Home, Connections, Agent Config, Action Log, Pending Approvals, Settings)
- `agent/` — LangGraph agent and tools (Gmail, Telegram, HubSpot, Notion, search)
- `integrations/` — Gmail, Telegram, HubSpot, Notion, search
- `db/` — PostgreSQL models, migrations, credential storage
- `worker/` — Redis queue consumer
- `bot/` — Telegram webhook (FastAPI)
- `core/` — Encryption, config

## Security

- All API keys and credentials are encrypted (Fernet) before storing in the DB.
- Encryption key is in `ENCRYPTION_KEY` env var only.
- No credentials in logs; all DB queries are parameterized.

## License

Portfolio project — use as reference only.
