"""
agent/approval.py — Approval gate with Redis pub/sub wait.
When an agent tool requires user approval, this module:
  1. Creates a pending_approval DB row.
  2. Sends a Telegram message with Approve/Reject inline buttons.
  3. Subscribes to Redis channel and waits up to APPROVAL_TIMEOUT_SECONDS.
  4. Returns True (approved), False (rejected), or None (timeout/expired).
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import redis.asyncio as aioredis

from core.config import get_settings
from core.encryption import decrypt_dict
from db.base import session_context
from db.models import Integration, PendingApproval

log = logging.getLogger(__name__)

APPROVAL_TIMEOUT_SECONDS = 600  # 10 minutes
REDIS_APPROVAL_CHANNEL_PREFIX = "toora:approvals:"

DEFAULT_USER_ID = 1


async def _get_telegram_creds() -> Optional[Dict[str, str]]:
    async with session_context() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(Integration).where(
                Integration.user_id == DEFAULT_USER_ID,
                Integration.platform == "telegram",
                Integration.status == "connected",
            )
        )
        integration = result.scalar_one_or_none()
        if not integration:
            return None
        return decrypt_dict(integration.encrypted_credentials)


async def require_approval(
    run_id: int,
    action_description: str,
    full_context: Dict[str, Any],
) -> Optional[bool]:
    """
    Create a pending approval, notify via Telegram, and wait for decision.
    Returns True if approved, False if rejected, None if timed out or error.
    """
    settings = get_settings(required=["DATABASE_URL", "REDIS_URL"])

    # Create DB record
    expires = datetime.now(tz=timezone.utc) + timedelta(seconds=APPROVAL_TIMEOUT_SECONDS)
    async with session_context() as db:
        approval = PendingApproval(
            run_id=run_id,
            action_description=action_description,
            full_context=full_context,
            expires_at=expires,
            status="pending",
        )
        db.add(approval)
        await db.flush()
        approval_id = approval.id
        await db.refresh(approval)

    log.info("Approval %d created for run %d: %s", approval_id, run_id, action_description)

    # Send Telegram approval request
    tg_creds = await _get_telegram_creds()
    if tg_creds:
        from agent.integrations.telegram import build_approval_keyboard, send_message
        text = (
            f"*🤖 Toora needs your approval*\n\n"
            f"*Action:* {action_description}\n\n"
            f"*Context:*\n```{json.dumps(full_context, indent=2)[:500]}```\n\n"
            f"_Expires in 10 minutes_"
        )
        try:
            resp = await send_message(tg_creds, text, build_approval_keyboard(approval_id))
            tg_msg_id = resp.get("result", {}).get("message_id")
            if tg_msg_id:
                async with session_context() as db:
                    from sqlalchemy import select
                    result = await db.execute(
                        select(PendingApproval).where(PendingApproval.id == approval_id)
                    )
                    row = result.scalar_one_or_none()
                    if row:
                        row.telegram_message_id = tg_msg_id
        except Exception as exc:
            log.error("Failed to send Telegram approval message: %s", exc)

    # Subscribe to Redis and wait
    r = aioredis.from_url(settings.redis_url, decode_responses=True)
    channel = f"{REDIS_APPROVAL_CHANNEL_PREFIX}{approval_id}"
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)

    decision: Optional[bool] = None
    try:
        deadline = asyncio.get_event_loop().time() + APPROVAL_TIMEOUT_SECONDS
        async for message in pubsub.listen():
            if asyncio.get_event_loop().time() > deadline:
                break
            if message["type"] == "message":
                data = json.loads(message["data"])
                decision = data.get("approved")
                break
    except asyncio.TimeoutError:
        pass
    finally:
        await pubsub.unsubscribe(channel)
        await r.aclose()

    # Update DB if timed out
    if decision is None:
        async with session_context() as db:
            from sqlalchemy import select
            result = await db.execute(
                select(PendingApproval).where(PendingApproval.id == approval_id)
            )
            row = result.scalar_one_or_none()
            if row and row.status == "pending":
                row.status = "expired"
                row.resolved_at = datetime.now(tz=timezone.utc)

    return decision
