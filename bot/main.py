"""
bot/main.py — FastAPI Telegram webhook listener.
Receives updates from Telegram and dispatches callback_query and message events.
"""

from __future__ import annotations

import logging
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Header, HTTPException, Request

from bot.handler import handle_callback_query, handle_message

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Toora Bot", version="2.0.0")

_WEBHOOK_SECRET = os.environ.get("TELEGRAM_WEBHOOK_SECRET", "")


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/webhook/telegram")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str = Header(default=""),
):
    # Verify webhook secret if configured
    if _WEBHOOK_SECRET and x_telegram_bot_api_secret_token != _WEBHOOK_SECRET:
        raise HTTPException(status_code=403, detail="Invalid webhook secret.")

    update = await request.json()
    log.debug("Telegram update received: %s", update)

    if "callback_query" in update:
        await handle_callback_query(update["callback_query"])
    elif "message" in update:
        await handle_message(update["message"])

    # Always return 200 so Telegram stops retrying
    return {"ok": True}
