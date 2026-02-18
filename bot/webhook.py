"""
FastAPI app: Telegram webhook receiver.
On callback_query (Approve/Reject), updates pending_approvals and optionally notifies via Redis.
"""

from __future__ import annotations

import os
import sys
from typing import Any, Dict

# Ensure project root on path when run via uvicorn
_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)
os.chdir(_root)
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(_root, ".env"))
except ImportError:
    pass

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

# Optional: run DB/Redis only when needed
def _get_user_telegram_creds(user_id: int):
    from db.models import get_decrypted_credentials
    return get_decrypted_credentials(user_id, "telegram")

def _set_approval(approval_id: int, approved: bool):
    from db.models import set_approval_decision
    set_approval_decision(approval_id, approved)

def _publish_approval_decision(approval_id: int, approved: bool):
    """Publish to Redis so worker can stop polling."""
    try:
        import redis
        import json
        r = redis.from_url(os.environ.get("REDIS_URL", ""))
        r.publish("toora:approvals", json.dumps({"approval_id": approval_id, "approved": approved}))
    except Exception:
        pass

app = FastAPI(title="Toora Telegram Bot")


@app.post("/webhook/telegram")
async def telegram_webhook(request: Request):
    """Receive Telegram updates. Handle only callback_query for Approve/Reject."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(content={"ok": False}, status_code=400)

    # Telegram sends either message or callback_query
    callback = body.get("callback_query")
    if callback:
        data = callback.get("data", "")
        id_str = str(callback.get("id", ""))
        approval_user_id: int | None = None
        if data.startswith("approve_"):
            try:
                approval_id = int(data.split("_", 1)[1])
                from db.models import get_pending_approval
                pa = get_pending_approval(approval_id)
                if pa:
                    approval_user_id = pa["user_id"]
                _set_approval(approval_id, True)
                _publish_approval_decision(approval_id, True)
            except (ValueError, TypeError):
                pass
            if approval_user_id:
                _answer_callback(approval_user_id, id_str, "Approved")
        elif data.startswith("reject_"):
            try:
                approval_id = int(data.split("_", 1)[1])
                from db.models import get_pending_approval
                pa = get_pending_approval(approval_id)
                if pa:
                    approval_user_id = pa["user_id"]
                _set_approval(approval_id, False)
                _publish_approval_decision(approval_id, False)
            except (ValueError, TypeError):
                pass
            if approval_user_id:
                _answer_callback(approval_user_id, id_str, "Rejected")

    return Response(content="ok")


def _answer_callback(approval_user_id: int, callback_query_id: str, text: str):
    """Answer callback via Telegram API using the approval owner's bot token."""
    from db.models import get_decrypted_credentials
    from integrations.telegram import answer_callback_query
    creds = get_decrypted_credentials(approval_user_id, "telegram")
    if not creds:
        return
    answer_callback_query(creds["bot_token"], callback_query_id, text)


@app.get("/health")
async def health():
    return {"status": "ok"}
