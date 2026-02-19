"""
backend/services/agent_svc.py — Business logic for agent control and configuration.
"""

from __future__ import annotations

import json
import logging
from typing import Optional

import redis.asyncio as aioredis
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.models import AgentConfig, AgentRun
from backend.schemas import AgentConfigOut, AgentConfigUpdate, AgentStatusOut

log = logging.getLogger(__name__)

DEFAULT_USER_ID = 1
REDIS_JOB_QUEUE = "toora:agent_jobs"
REDIS_STATUS_KEY = "toora:agent_status"


async def push_run_job(redis_url: str) -> None:
    """Push a manual agent run job onto the Redis queue."""
    r = aioredis.from_url(redis_url, decode_responses=True)
    payload = json.dumps({"user_id": DEFAULT_USER_ID, "triggered_by": "manual"})
    await r.rpush(REDIS_JOB_QUEUE, payload)
    await r.aclose()
    log.info("Agent job pushed to Redis queue.")


async def get_status(redis_url: str, db: AsyncSession) -> AgentStatusOut:
    r = aioredis.from_url(redis_url, decode_responses=True)
    raw = await r.get(REDIS_STATUS_KEY)
    await r.aclose()

    status = "idle"
    run_id: Optional[int] = None
    if raw:
        try:
            data = json.loads(raw)
            status = data.get("status", "idle")
            run_id = data.get("run_id")
        except Exception:
            pass

    # Fetch last run for context
    result = await db.execute(
        select(AgentRun)
        .where(AgentRun.user_id == DEFAULT_USER_ID)
        .order_by(AgentRun.triggered_at.desc())
        .limit(1)
    )
    last_run = result.scalar_one_or_none()
    return AgentStatusOut(status=status, run_id=run_id, last_run=last_run)


async def get_config(db: AsyncSession) -> AgentConfigOut:
    result = await db.execute(
        select(AgentConfig).where(AgentConfig.user_id == DEFAULT_USER_ID)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        return AgentConfigOut(
            enabled_tools={},
            schedule="manual",
            system_prompt=None,
            approval_rules={},
        )
    return AgentConfigOut.model_validate(cfg)


async def update_config(db: AsyncSession, data: AgentConfigUpdate) -> AgentConfigOut:
    result = await db.execute(
        select(AgentConfig).where(AgentConfig.user_id == DEFAULT_USER_ID)
    )
    cfg = result.scalar_one_or_none()
    if not cfg:
        cfg = AgentConfig(user_id=DEFAULT_USER_ID, enabled_tools={}, approval_rules={})
        db.add(cfg)

    if data.enabled_tools is not None:
        cfg.enabled_tools = data.enabled_tools
    if data.schedule is not None:
        cfg.schedule = data.schedule
    if data.system_prompt is not None:
        cfg.system_prompt = data.system_prompt
    if data.approval_rules is not None:
        cfg.approval_rules = data.approval_rules

    await db.flush()
    await db.refresh(cfg)
    return AgentConfigOut.model_validate(cfg)
