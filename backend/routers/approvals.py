"""
backend/routers/approvals.py — /api/approvals routes.
"""

from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import ApprovalOut
from backend.services import approval_svc
from backend.ws.manager import ws_manager
from db.base import get_session

router = APIRouter(prefix="/api/approvals", tags=["approvals"])


@router.get("", response_model=List[ApprovalOut])
async def list_approvals(
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session),
):
    return await approval_svc.list_approvals(db, status)


@router.post("/{approval_id}/approve", response_model=ApprovalOut)
async def approve(
    approval_id: int,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    try:
        result = await approval_svc.resolve(
            db, approval_id, approved=True, redis_url=request.app.state.redis_url
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    await ws_manager.broadcast({"type": "approval_resolved", "data": result.model_dump(mode="json")})
    return result


@router.post("/{approval_id}/reject", response_model=ApprovalOut)
async def reject(
    approval_id: int,
    request: Request,
    db: AsyncSession = Depends(get_session),
):
    try:
        result = await approval_svc.resolve(
            db, approval_id, approved=False, redis_url=request.app.state.redis_url
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    await ws_manager.broadcast({"type": "approval_resolved", "data": result.model_dump(mode="json")})
    return result
