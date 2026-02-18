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

## Required: Worker start command and build settings

The repo has one `railway.toml` (used by **web**). The **worker** service must be configured in the Railway dashboard:

1. Open project **Toora** → **worker** service → **Settings**.
2. **Build**
   - Leave **Build Command empty** (do not set it to `python -m worker.run`). If it is set, clear it. The build must only install dependencies; running the worker at build time fails because `DATABASE_URL` is not available during build.
3. **Deploy / Start**
   - Set **Custom start command** (Start Command) to:
     ```bash
     python -m worker.run
     ```
4. **Health check**
   - Disable the health check for the worker (or set to a custom check). The worker does not serve HTTP or `/health`; the default health check would always fail and mark the deployment failed.
5. Save and redeploy the worker.

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

---

## Deployment issues (worker)

**Symptom:** Worker deployment fails with `ValueError: DATABASE_URL environment variable is not set` during **build**.

**Cause:** The worker service had **Build Command** set to `python -m worker.run`. Railway runs the build command during the Docker image build, when no runtime env vars (like `DATABASE_URL`) exist, so the worker crashes and the build fails.

**Fix:**

1. **Worker** → **Settings** → **Build**: clear **Build Command** (leave empty).
2. **Worker** → **Settings** → **Deploy**: set **Start Command** to `python -m worker.run`.
3. **Worker** → **Settings** → **Health check**: disable it (worker has no HTTP server).
4. Ensure **DATABASE_URL**, **REDIS_URL**, **ENCRYPTION_KEY**, and **OPENROUTER_API_KEY** are set (project or service variables) so the worker can start at runtime.
