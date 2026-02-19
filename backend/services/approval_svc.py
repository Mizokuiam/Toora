"""
backend/services/approval_svc.py — Approval resolution logic.
Called by both the dashboard API and the Telegram bot handler.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import List, Optional

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import ApprovalOut
from db.models import PendingApproval

log = logging.getLogger(__name__)

REDIS_APPROVAL_CHANNEL_PREFIX = "toora:approvals:"


async def list_approvals(
    db: AsyncSession, status: Optional[str] = None
) -> List[ApprovalOut]:
    query = select(PendingApproval).order_by(PendingApproval.created_at.desc())
    if status:
        query = query.where(PendingApproval.status == status)
    rows = await db.execute(query)
    return [ApprovalOut.model_validate(r) for r in rows.scalars().all()]


async def resolve(
    db: AsyncSession,
    approval_id: int,
    approved: bool,
    redis_url: Optional[str] = None,
) -> ApprovalOut:
    """Mark an approval as approved or rejected and publish to Redis."""
    result = await db.execute(
        select(PendingApproval).where(PendingApproval.id == approval_id)
    )
    approval: Optional[PendingApproval] = result.scalar_one_or_none()
    if not approval:
        raise ValueError(f"Approval {approval_id} not found.")

    approval.status = "approved" if approved else "rejected"
    approval.resolved_at = datetime.now(tz=timezone.utc)
    await db.flush()
    await db.refresh(approval)

    # Notify the agent worker via Redis pub/sub
    if redis_url:
        try:
            r = aioredis.from_url(redis_url, decode_responses=True)
            channel = f"{REDIS_APPROVAL_CHANNEL_PREFIX}{approval_id}"
            await r.publish(channel, json.dumps({"approved": approved}))
            await r.aclose()
        except Exception as exc:
            log.error("Failed to publish approval decision to Redis: %s", exc)

    return ApprovalOut.model_validate(approval)
