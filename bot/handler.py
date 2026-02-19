"""
bot/handler.py — Parses Telegram callback_query and message events.
Resolves approvals in DB and publishes to Redis; responds to /start, /brief, /status.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict

import httpx

from core.config import get_settings
from db.base import session_context
from backend.services.approval_svc import resolve

log = logging.getLogger(__name__)

BACKEND_URL = os.environ.get("BACKEND_URL", "https://toora-production.up.railway.app")


async def handle_message(message: Dict[str, Any]) -> None:
    """Process Telegram message updates (e.g. /start, /brief, /status)."""
    text = (message.get("text") or "").strip()
    chat_id = message.get("chat", {}).get("id")
    if not chat_id:
        return

    if text in ("/start", "/help"):
        reply = (
            "👋 *Welcome to Toora!*\n\n"
            "I'm your AI executive assistant. Here's what you can do:\n\n"
            "• `/brief` — Get a fresh briefing (reads inbox, summarizes)\n"
            "• `/status` — Check if the agent is running\n\n"
            "When the agent needs your approval (e.g. to send an email), "
            "I'll send you buttons to approve or reject.\n\n"
            "You can also use the [Dashboard](https://frontend-production-8833b.up.railway.app) for more."
        )
        await _send_message(chat_id, reply)
        return

    if text == "/brief":
        ok = await _trigger_agent_run()
        reply = "🚀 Agent started! You'll get your briefing shortly." if ok else "⚠️ Could not start agent. Check the dashboard."
        await _send_message(chat_id, reply)
        return

    if text == "/status":
        status = await _get_agent_status()
        reply = f"📊 *Agent status:* {status}"
        await _send_message(chat_id, reply)
        return


async def _trigger_agent_run() -> bool:
    """POST to backend to queue an agent run."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.post(f"{BACKEND_URL.rstrip('/')}/api/agent/run", json={})
            return r.status_code == 200
    except Exception as exc:
        log.error("Failed to trigger agent run: %s", exc)
        return False


async def _get_agent_status() -> str:
    """GET agent status from backend."""
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(f"{BACKEND_URL.rstrip('/')}/api/agent/status")
            if r.status_code == 200:
                data = r.json()
                return data.get("status", "unknown")
    except Exception as exc:
        log.error("Failed to get agent status: %s", exc)
    return "unknown"


async def handle_run_agent_callback(chat_id: int, callback_id: str) -> None:
    """Handle 'run_agent' callback - trigger job and answer."""
    ok = await _trigger_agent_run()
    text = "🚀 Started! Briefing on its way 📬" if ok else "⚠️ Could not start. Try the dashboard."
    await _answer_callback(callback_id, text)
    if ok:
        await _send_message(chat_id, "Agent is running. You'll get your briefing in a moment.")


def _parse_callback_data(data: str) -> tuple[int, bool] | None:
    """
    Expected callback data format: 'approve:123' or 'reject:123'
    Returns (approval_id, approved) or None if malformed.
    """
    try:
        action, raw_id = data.split(":", 1)
        approval_id = int(raw_id)
        if action == "approve":
            return approval_id, True
        elif action == "reject":
            return approval_id, False
    except Exception:
        pass
    return None


async def handle_callback_query(callback_query: Dict[str, Any]) -> None:
    """Process a Telegram callback_query update."""
    data = callback_query.get("data", "")
    chat_id = callback_query.get("message", {}).get("chat", {}).get("id")
    callback_id = callback_query.get("id")

    if data == "run_agent":
        if chat_id:
            await handle_run_agent_callback(chat_id, callback_id)
        return

    parsed = _parse_callback_data(data)
    if parsed is None:
        log.warning("Unrecognised callback data: %r", data)
        return

    settings = get_settings(required=["DATABASE_URL", "REDIS_URL"])
    approval_id, approved = parsed

    async with session_context() as db:
        try:
            await resolve(db, approval_id, approved, redis_url=settings.redis_url)
            log.info(
                "Approval %d %s via Telegram.",
                approval_id,
                "approved" if approved else "rejected",
            )
        except ValueError as exc:
            log.error("Approval resolution error: %s", exc)
            return

    # Answer the Telegram callback to remove the loading spinner on the button
    callback_id = callback_query.get("id")
    text = "✅ Approved!" if approved else "❌ Rejected."
    await _answer_callback(callback_id, text)


async def _get_telegram_bot_token() -> str:
    """Read the Telegram bot token from the encrypted integrations DB row."""
    try:
        from sqlalchemy import select
        from db.models import Integration
        from core.encryption import decrypt_dict
        async with session_context() as db:
            result = await db.execute(
                select(Integration).where(
                    Integration.platform == "telegram",
                    Integration.status == "connected",
                )
            )
            row = result.scalar_one_or_none()
            if row:
                creds = decrypt_dict(row.encrypted_credentials)
                return creds.get("bot_token", "")
    except Exception as exc:
        log.error("Failed to load Telegram token from DB: %s", exc)
    return ""


async def _answer_callback(callback_query_id: str, text: str) -> None:
    """Answer the Telegram callback query to dismiss the loading state."""
    tg_token = await _get_telegram_bot_token()
    if not tg_token:
        return
    url = f"https://api.telegram.org/bot{tg_token}/answerCallbackQuery"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"callback_query_id": callback_query_id, "text": text})
    except Exception as exc:
        log.error("Failed to answer Telegram callback: %s", exc)


async def _send_message(chat_id: int, text: str) -> None:
    """Send a text message to a Telegram chat."""
    tg_token = await _get_telegram_bot_token()
    if not tg_token:
        return
    url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
    except Exception as exc:
        log.error("Failed to send Telegram message: %s", exc)
