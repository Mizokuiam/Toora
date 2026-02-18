# Procfile for Railway (use per-service start in dashboard or railway.toml)
# Service A — Telegram bot webhook
web: uvicorn bot.webhook:app --host 0.0.0.0 --port $PORT

# Service B — Agent worker (run as separate Railway service with command override)
worker: python -m worker.run
