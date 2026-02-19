"""
backend/services/integration_svc.py — Business logic for integration management.
Encrypts credentials before writing to DB; decrypts for connection tests.
"""

from __future__ import annotations

import importlib
import logging
from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.encryption import decrypt_dict, encrypt_dict
from db.models import Integration

log = logging.getLogger(__name__)

DEFAULT_USER_ID = 1


async def list_integrations(db: AsyncSession) -> List[Integration]:
    result = await db.execute(
        select(Integration).where(Integration.user_id == DEFAULT_USER_ID)
    )
    return list(result.scalars().all())


async def save_credentials(
    db: AsyncSession, platform: str, credentials: Dict[str, str]
) -> Integration:
    """Encrypt and upsert credentials for a platform."""
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == DEFAULT_USER_ID,
            Integration.platform == platform,
        )
    )
    integration: Integration | None = result.scalar_one_or_none()
    encrypted = encrypt_dict(credentials)
    now = datetime.now(tz=timezone.utc)

    if integration:
        integration.encrypted_credentials = encrypted
        integration.connected_at = now
        integration.status = "connected"
    else:
        integration = Integration(
            user_id=DEFAULT_USER_ID,
            platform=platform,
            encrypted_credentials=encrypted,
            connected_at=now,
            status="connected",
        )
        db.add(integration)

    await db.flush()
    await db.refresh(integration)
    return integration


async def disconnect_platform(db: AsyncSession, platform: str) -> bool:
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == DEFAULT_USER_ID,
            Integration.platform == platform,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        return False
    integration.status = "disconnected"
    return True


async def test_connection(db: AsyncSession, platform: str) -> Dict[str, object]:
    """Decrypt credentials and call the relevant integration test function."""
    result = await db.execute(
        select(Integration).where(
            Integration.user_id == DEFAULT_USER_ID,
            Integration.platform == platform,
        )
    )
    integration = result.scalar_one_or_none()
    if not integration:
        return {"success": False, "message": "No credentials saved for this platform."}

    try:
        creds = decrypt_dict(integration.encrypted_credentials)
    except Exception as exc:
        log.error("Decryption error for %s: %s", platform, exc)
        return {"success": False, "message": "Failed to decrypt credentials."}

    # Dynamically load the integration module
    try:
        mod = importlib.import_module(f"agent.integrations.{platform}")
        result_msg = await mod.test_connection(creds)
        return {"success": True, "message": result_msg}
    except ImportError:
        return {"success": False, "message": f"Integration module '{platform}' not found."}
    except Exception as exc:
        log.error("Connection test failed for %s: %s", platform, exc)
        return {"success": False, "message": str(exc)}
