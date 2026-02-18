"""
Telegram Bot API: send messages and approval requests with inline keyboards.
Credentials: bot_token, chat_id. Never logs tokens.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

import requests

BASE_URL = "https://api.telegram.org/bot{token}/{method}"


def _url(token: str, method: str) -> str:
    return BASE_URL.format(token=token, method=method)


def test_connection(creds: Dict[str, Any]) -> tuple[bool, str]:
    """Test bot token with getMe. creds: bot_token, chat_id."""
    try:
        r = requests.get(_url(creds["bot_token"], "getMe"), timeout=10)
        data = r.json()
        if not data.get("ok"):
            return False, data.get("description", "Unknown error")
        return True, "Bot connected"
    except Exception as e:
        return False, str(e)


def send_message(creds: Dict[str, Any], text: str, parse_mode: Optional[str] = "HTML") -> tuple[bool, Optional[int], str]:
    """
    Send text to chat_id. Returns (success, message_id, error_message).
    """
    try:
        payload: Dict[str, Any] = {"chat_id": creds["chat_id"], "text": text}
        if parse_mode:
            payload["parse_mode"] = parse_mode
        r = requests.post(_url(creds["bot_token"], "sendMessage"), json=payload, timeout=10)
        data = r.json()
        if not data.get("ok"):
            return False, None, data.get("description", "Unknown error")
        return True, data.get("result", {}).get("message_id"), ""
    except Exception as e:
        return False, None, str(e)


def send_approval_request(
    creds: Dict[str, Any],
    text: str,
    approval_id: int,
) -> tuple[bool, Optional[int], str]:
    """
    Send message with Approve/Reject inline buttons.
    Callback data: approve_{id} and reject_{id}.
    Returns (success, message_id, error_message).
    """
    try:
        payload: Dict[str, Any] = {
            "chat_id": creds["chat_id"],
            "text": text,
            "parse_mode": "HTML",
            "reply_markup": {
                "inline_keyboard": [
                    [
                        {"text": "✅ Approve", "callback_data": f"approve_{approval_id}"},
                        {"text": "❌ Reject", "callback_data": f"reject_{approval_id}"},
                    ]
                ]
            },
        }
        r = requests.post(_url(creds["bot_token"], "sendMessage"), json=payload, timeout=10)
        data = r.json()
        if not data.get("ok"):
            return False, None, data.get("description", "Unknown error")
        return True, data.get("result", {}).get("message_id"), ""
    except Exception as e:
        return False, None, str(e)


def answer_callback_query(token: str, callback_query_id: str, text: Optional[str] = None) -> None:
    """Answer callback so Telegram stops loading state."""
    try:
        payload: Dict[str, Any] = {"callback_query_id": callback_query_id}
        if text:
            payload["text"] = text
        requests.post(_url(token, "answerCallbackQuery"), json=payload, timeout=5)
    except Exception:
        pass
