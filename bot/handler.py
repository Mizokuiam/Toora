"""
bot/handler.py — Parses Telegram callback_query events, resolves approvals in DB,
and publishes the decision to Redis so the agent worker can proceed.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict

import httpx
import redis.asyncio as aioredis

from core.config import get_settings
from db.base import session_context
from backend.services.approval_svc import resolve

log = logging.getLogger(__name__)


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
    settings = get_settings(required=["DATABASE_URL", "REDIS_URL"])
    data = callback_query.get("data", "")
    parsed = _parse_callback_data(data)

    if parsed is None:
        log.warning("Unrecognised callback data: %r", data)
        return

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
    await _answer_callback(callback_id, text, settings.openrouter_api_key)


async def _answer_callback(callback_query_id: str, text: str, bot_token: str) -> None:
    """Answer the Telegram callback query to dismiss the loading state."""
    # bot_token here is actually the Telegram bot token — loaded from a dedicated env var
    telegram_token = get_settings.__wrapped__ if False else None  # sentinel
    import os
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not tg_token:
        return
    url = f"https://api.telegram.org/bot{tg_token}/answerCallbackQuery"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            await client.post(url, json={"callback_query_id": callback_query_id, "text": text})
    except Exception as exc:
        log.error("Failed to answer Telegram callback: %s", exc)
