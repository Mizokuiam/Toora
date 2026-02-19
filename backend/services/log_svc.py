"""
backend/services/log_svc.py — Paginated action log queries.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import ActionLogOut, PaginatedLogs
from db.models import ActionLog, AgentRun

DEFAULT_USER_ID = 1


async def list_logs(
    db: AsyncSession,
    page: int = 1,
    per_page: int = 25,
    tool: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
) -> PaginatedLogs:
    query = (
        select(ActionLog)
        .join(AgentRun, ActionLog.run_id == AgentRun.id)
        .where(AgentRun.user_id == DEFAULT_USER_ID)
    )
    if tool:
        query = query.where(ActionLog.tool_used == tool)
    if status:
        query = query.where(ActionLog.approval_status == status)
    if date_from:
        query = query.where(ActionLog.timestamp >= date_from)
    if date_to:
        query = query.where(ActionLog.timestamp <= date_to)

    count_q = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_q)
    total: int = total_result.scalar_one()

    paged = (
        query.order_by(ActionLog.timestamp.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    rows = await db.execute(paged)
    items: List[ActionLogOut] = [
        ActionLogOut.model_validate(r) for r in rows.scalars().all()
    ]
    return PaginatedLogs(items=items, total=total, page=page, per_page=per_page)


async def get_log(db: AsyncSession, log_id: int) -> Optional[ActionLogOut]:
    result = await db.execute(select(ActionLog).where(ActionLog.id == log_id))
    row = result.scalar_one_or_none()
    if not row:
        return None
    return ActionLogOut.model_validate(row)
