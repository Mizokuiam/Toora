"""
backend/routers/stats.py — /api/stats routes.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import TodayStats
from db.base import get_session
from db.models import ActionLog, AgentRun, PendingApproval

router = APIRouter(prefix="/api/stats", tags=["stats"])

DEFAULT_USER_ID = 1


@router.get("/today", response_model=TodayStats)
async def today_stats(db: AsyncSession = Depends(get_session)):
    today_start = datetime.now(tz=timezone.utc).replace(
        hour=0, minute=0, second=0, microsecond=0
    )

    # Emails processed = read_gmail tool calls today
    emails_q = (
        select(func.count())
        .select_from(ActionLog)
        .join(AgentRun, ActionLog.run_id == AgentRun.id)
        .where(
            AgentRun.user_id == DEFAULT_USER_ID,
            ActionLog.tool_used == "read_gmail",
            ActionLog.timestamp >= today_start,
        )
    )
    emails: int = (await db.execute(emails_q)).scalar_one()

    # Tasks created = create_notion_task calls today
    tasks_q = (
        select(func.count())
        .select_from(ActionLog)
        .join(AgentRun, ActionLog.run_id == AgentRun.id)
        .where(
            AgentRun.user_id == DEFAULT_USER_ID,
            ActionLog.tool_used == "create_notion_task",
            ActionLog.timestamp >= today_start,
        )
    )
    tasks: int = (await db.execute(tasks_q)).scalar_one()

    # Pending approvals
    pending_q = select(func.count()).select_from(PendingApproval).where(
        PendingApproval.status == "pending"
    )
    pending: int = (await db.execute(pending_q)).scalar_one()

    # Last run
    last_run_q = (
        select(AgentRun.triggered_at)
        .where(AgentRun.user_id == DEFAULT_USER_ID)
        .order_by(AgentRun.triggered_at.desc())
        .limit(1)
    )
    last_run_result = await db.execute(last_run_q)
    last_run_at = last_run_result.scalar_one_or_none()

    return TodayStats(
        emails_processed=emails,
        tasks_created=tasks,
        approvals_pending=pending,
        last_run_at=last_run_at,
    )
