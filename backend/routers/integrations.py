"""
backend/routers/integrations.py — /api/integrations routes.
"""

from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from backend.schemas import CredentialSaveRequest, IntegrationOut, TestConnectionResult
from backend.services import integration_svc
from db.base import get_session

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("", response_model=List[IntegrationOut])
async def list_integrations(db: AsyncSession = Depends(get_session)):
    return await integration_svc.list_integrations(db)


@router.post("/{platform}", response_model=IntegrationOut)
async def save_credentials(
    platform: str,
    body: CredentialSaveRequest,
    db: AsyncSession = Depends(get_session),
):
    return await integration_svc.save_credentials(db, platform, body.credentials)


@router.delete("/{platform}")
async def disconnect(platform: str, db: AsyncSession = Depends(get_session)):
    ok = await integration_svc.disconnect_platform(db, platform)
    if not ok:
        raise HTTPException(status_code=404, detail="Integration not found.")
    return {"message": f"{platform} disconnected."}


@router.post("/{platform}/test", response_model=TestConnectionResult)
async def test_connection(platform: str, db: AsyncSession = Depends(get_session)):
    result = await integration_svc.test_connection(db, platform)
    return TestConnectionResult(**result)


@router.post("/telegram/register-webhook")
async def register_telegram_webhook(db: AsyncSession = Depends(get_session)):
    """Register the Telegram webhook using stored credentials. Call after connecting Telegram."""
    result = await integration_svc.register_telegram_webhook(db)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result
