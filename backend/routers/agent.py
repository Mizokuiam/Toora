"""
backend/routers/agent.py — /api/agent routes.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import AgentConfigOut, AgentConfigUpdate, AgentStatusOut
from backend.services import agent_svc
from db.base import get_session

router = APIRouter(prefix="/api/agent", tags=["agent"])


@router.post("/run")
async def run_agent(request: Request):
    redis_url: str = request.app.state.redis_url
    await agent_svc.push_run_job(redis_url)
    return {"message": "Agent job queued."}


@router.get("/status", response_model=AgentStatusOut)
async def get_status(request: Request, db: AsyncSession = Depends(get_session)):
    return await agent_svc.get_status(request.app.state.redis_url, db)


@router.get("/config", response_model=AgentConfigOut)
async def get_config(db: AsyncSession = Depends(get_session)):
    return await agent_svc.get_config(db)


@router.put("/config", response_model=AgentConfigOut)
async def update_config(
    body: AgentConfigUpdate, db: AsyncSession = Depends(get_session)
):
    return await agent_svc.update_config(db, body)
