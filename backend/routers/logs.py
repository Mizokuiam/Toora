"""
backend/routers/logs.py — /api/logs routes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import ActionLogOut, PaginatedLogs
from backend.services import log_svc
from db.base import get_session

router = APIRouter(prefix="/api/logs", tags=["logs"])


@router.get("", response_model=PaginatedLogs)
async def list_logs(
    page: int = Query(1, ge=1),
    per_page: int = Query(25, ge=1, le=100),
    tool: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_session),
):
    return await log_svc.list_logs(db, page, per_page, tool, status, date_from, date_to)


@router.get("/{log_id}", response_model=ActionLogOut)
async def get_log(log_id: int, db: AsyncSession = Depends(get_session)):
    entry = await log_svc.get_log(db, log_id)
    if not entry:
        raise HTTPException(status_code=404, detail="Log entry not found.")
    return entry
