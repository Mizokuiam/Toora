"""
agent/integrations/telegram.py — Telegram Bot API helpers.
Credentials: {"bot_token": "...", "chat_id": "..."}
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

import httpx

API_BASE = "https://api.telegram.org/bot{token}/{method}"


def _url(token: str, method: str) -> str:
    return API_BASE.format(token=token, method=method)


async def test_connection(creds: Dict[str, str]) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(_url(creds["bot_token"], "getMe"))
        r.raise_for_status()
        data = r.json()
        return f"Telegram bot connected: @{data['result']['username']}"


async def send_message(
    creds: Dict[str, str],
    text: str,
    inline_keyboard: Optional[List[List[Dict[str, str]]]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "chat_id": creds["chat_id"],
        "text": text,
        "parse_mode": "Markdown",
    }
    if inline_keyboard:
        payload["reply_markup"] = {"inline_keyboard": inline_keyboard}

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(_url(creds["bot_token"], "sendMessage"), json=payload)
        r.raise_for_status()
        return r.json()


async def register_webhook(bot_token: str, webhook_url: str, secret_token: Optional[str] = None) -> str:
    """Register Telegram webhook. Returns result message."""
    params: Dict[str, str] = {"url": webhook_url}
    if secret_token:
        params["secret_token"] = secret_token
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(_url(bot_token, "setWebhook"), params=params)
        r.raise_for_status()
        data = r.json()
        if data.get("ok"):
            return "Webhook registered successfully."
        return data.get("description", "Unknown error")


def build_approval_keyboard(approval_id: int) -> List[List[Dict[str, str]]]:
    return [
        [
            {"text": "✅ Approve", "callback_data": f"approve:{approval_id}"},
            {"text": "❌ Reject", "callback_data": f"reject:{approval_id}"},
        ]
    ]
