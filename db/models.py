"""
Database models and query helpers.
Credentials are stored encrypted; decrypt only when needed. No credentials in logs.
All queries use parameterized statements.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from db.connection import get_cursor
from core.encryption import encrypt_value, decrypt_value, decrypt_json


# Default single user for portfolio (single-tenant)
DEFAULT_USER_EXTERNAL_ID = "toora_default_user"


def get_or_create_user(external_id: str = DEFAULT_USER_EXTERNAL_ID) -> int:
    """Get or create user by external_id. Returns user_id."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id FROM users WHERE external_id = %s",
            (external_id,),
        )
        row = cur.fetchone()
        if row:
            return row[0]
        cur.execute(
            "INSERT INTO users (external_id) VALUES (%s) RETURNING id",
            (external_id,),
        )
        return cur.fetchone()[0]


def save_credentials(
    user_id: int,
    integration: str,
    payload: Dict[str, Any],
) -> None:
    """
    Encrypt and store credentials for an integration.
    payload is a dict of key/value (e.g. {"email": "...", "app_password": "..."}).
    """
    encrypted = encrypt_value(payload)
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO credentials (user_id, integration, encrypted_payload)
            VALUES (%s, %s, %s)
            ON CONFLICT (user_id, integration)
            DO UPDATE SET encrypted_payload = EXCLUDED.encrypted_payload, updated_at = NOW()
            """,
            (user_id, integration, encrypted),
        )


def get_decrypted_credentials(user_id: int, integration: str) -> Optional[Dict[str, Any]]:
    """
    Load and decrypt credentials for an integration.
    Returns None if not found or decryption fails.
    """
    with get_cursor() as cur:
        cur.execute(
            "SELECT encrypted_payload FROM credentials WHERE user_id = %s AND integration = %s",
            (user_id, integration),
        )
        row = cur.fetchone()
    if not row:
        return None
    try:
        return decrypt_json(row[0])
    except Exception:
        return None


def has_credentials(user_id: int, integration: str) -> bool:
    """Check if credentials exist for integration (without decrypting)."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT 1 FROM credentials WHERE user_id = %s AND integration = %s",
            (user_id, integration),
        )
        return cur.fetchone() is not None


# --- Agent runs ---


def create_agent_run(user_id: int) -> int:
    """Create a new agent run. Returns run_id."""
    with get_cursor() as cur:
        cur.execute(
            "INSERT INTO agent_runs (user_id, status) VALUES (%s, 'running') RETURNING id",
            (user_id,),
        )
        return cur.fetchone()[0]


def update_agent_run(run_id: int, status: str, summary: Optional[str] = None) -> None:
    """Update run status and optional summary."""
    with get_cursor() as cur:
        cur.execute(
            """
            UPDATE agent_runs
            SET status = %s, summary = %s, finished_at = NOW(), updated_at = NOW()
            WHERE id = %s
            """,
            (status, summary, run_id),
        )


def get_latest_agent_run(user_id: int) -> Optional[Dict[str, Any]]:
    """Get most recent agent run for dashboard."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, triggered_at, status, summary, finished_at
            FROM agent_runs WHERE user_id = %s ORDER BY triggered_at DESC LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    return {
        "id": row[0],
        "triggered_at": row[1],
        "status": row[2],
        "summary": row[3],
        "finished_at": row[4],
    }


def get_agent_run_status(user_id: int) -> str:
    """Return 'running', 'idle', or 'waiting_for_approval' for dashboard."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT status FROM agent_runs
            WHERE user_id = %s AND status IN ('running', 'waiting_for_approval')
            ORDER BY triggered_at DESC LIMIT 1
            """,
            (user_id,),
        )
        row = cur.fetchone()
    if row:
        return row[0]
    return "idle"


# --- Action log ---


def insert_action_log(
    user_id: int,
    tool_used: str,
    input_summary: Optional[str],
    input_full: Optional[Dict],
    output_summary: Optional[str],
    output_full: Optional[Dict],
    status: str = "completed",
    approval_status: Optional[str] = None,
    run_id: Optional[int] = None,
) -> int:
    """Insert action log entry. Returns log id."""
    import json
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO action_log
            (run_id, user_id, tool_used, input_summary, input_full, output_summary, output_full, status, approval_status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (
                run_id,
                user_id,
                tool_used,
                input_summary,
                json.dumps(input_full) if input_full else None,
                output_summary,
                json.dumps(output_full) if output_full else None,
                status,
                approval_status,
            ),
        )
        return cur.fetchone()[0]


def get_action_log(
    user_id: int,
    limit: int = 50,
    offset: int = 0,
    tool_filter: Optional[str] = None,
    status_filter: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Paginated action log with optional filters."""
    conditions = ["user_id = %s"]
    params: List[Any] = [user_id]
    if tool_filter:
        conditions.append("tool_used = %s")
        params.append(tool_filter)
    if status_filter:
        conditions.append("status = %s")
        params.append(status_filter)
    if date_from:
        conditions.append("created_at >= %s::date")
        params.append(date_from)
    if date_to:
        conditions.append("created_at <= %s::date")
        params.append(date_to)
    params.extend([limit, offset])
    with get_cursor() as cur:
        cur.execute(
            f"""
            SELECT id, run_id, tool_used, input_summary, output_summary, status, approval_status, created_at
            FROM action_log
            WHERE {' AND '.join(conditions)}
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
            """,
            params,
        )
        rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "run_id": r[1],
            "tool_used": r[2],
            "input_summary": r[3],
            "output_summary": r[4],
            "status": r[5],
            "approval_status": r[6],
            "created_at": r[7],
        }
        for r in rows
    ]


def get_action_log_detail(log_id: int, user_id: int) -> Optional[Dict[str, Any]]:
    """Get full details for one action log entry."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT id, run_id, tool_used, input_summary, input_full, output_summary, output_full, status, approval_status, created_at
            FROM action_log WHERE id = %s AND user_id = %s
            """,
            (log_id, user_id),
        )
        row = cur.fetchone()
    if not row:
        return None
    import json
    return {
        "id": row[0],
        "run_id": row[1],
        "tool_used": row[2],
        "input_summary": row[3],
        "input_full": json.loads(row[4]) if row[4] else None,
        "output_summary": row[5],
        "output_full": json.loads(row[6]) if row[6] else None,
        "status": row[7],
        "approval_status": row[8],
        "created_at": row[9],
    }


# --- Pending approvals ---


def create_pending_approval(
    user_id: int,
    run_id: Optional[int],
    action_description: str,
    action_type: str,
    action_payload: Dict[str, Any],
    telegram_message_id: Optional[int],
    expires_at_sec: int = 600,
) -> int:
    """Create pending approval. Default TTL 10 min. Returns approval id."""
    from datetime import datetime, timezone, timedelta
    expires = datetime.now(timezone.utc) + timedelta(seconds=expires_at_sec)
    import json
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO pending_approvals
            (user_id, run_id, action_description, action_type, action_payload, telegram_message_id, status, expires_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'pending', %s)
            RETURNING id
            """,
            (user_id, run_id, action_description, action_type, json.dumps(action_payload), telegram_message_id, expires),
        )
        return cur.fetchone()[0]


def set_approval_decision(approval_id: int, approved: bool, user_id: Optional[int] = None) -> bool:
    """Set approval to approved/rejected. Returns True if updated."""
    status = "approved" if approved else "rejected"
    with get_cursor() as cur:
        if user_id is not None:
            cur.execute(
                "UPDATE pending_approvals SET status = %s WHERE id = %s AND user_id = %s AND status = 'pending'",
                (status, approval_id, user_id),
            )
        else:
            cur.execute(
                "UPDATE pending_approvals SET status = %s WHERE id = %s AND status = 'pending'",
                (status, approval_id),
            )
        return cur.rowcount > 0


def get_pending_approval(approval_id: int) -> Optional[Dict[str, Any]]:
    """Get full pending approval by id."""
    with get_cursor() as cur:
        cur.execute(
            "SELECT id, run_id, user_id, action_description, action_type, action_payload, status, expires_at, created_at FROM pending_approvals WHERE id = %s",
            (approval_id,),
        )
        row = cur.fetchone()
    if not row:
        return None
    import json
    return {
        "id": row[0],
        "run_id": row[1],
        "user_id": row[2],
        "action_description": row[3],
        "action_type": row[4],
        "action_payload": json.loads(row[5]) if row[5] else row[5],
        "status": row[6],
        "expires_at": row[7],
        "created_at": row[8],
    }


def get_pending_approvals_for_user(user_id: int, include_expired: bool = False) -> List[Dict[str, Any]]:
    """List pending approvals for dashboard."""
    with get_cursor() as cur:
        if include_expired:
            cur.execute(
                """
                SELECT id, run_id, action_description, action_type, status, expires_at, created_at
                FROM pending_approvals WHERE user_id = %s ORDER BY created_at DESC
                """,
                (user_id,),
            )
        else:
            cur.execute(
                """
                SELECT id, run_id, action_description, action_type, status, expires_at, created_at
                FROM pending_approvals WHERE user_id = %s AND status = 'pending' AND expires_at > NOW()
                ORDER BY created_at DESC
                """,
                (user_id,),
            )
        rows = cur.fetchall()
    return [
        {
            "id": r[0],
            "run_id": r[1],
            "action_description": r[2],
            "action_type": r[3],
            "status": r[4],
            "expires_at": r[5],
            "created_at": r[6],
        }
        for r in rows
    ]


def expire_old_approvals() -> None:
    """Mark expired pending approvals as expired/skipped."""
    with get_cursor() as cur:
        cur.execute(
            "UPDATE pending_approvals SET status = 'expired' WHERE status = 'pending' AND expires_at <= NOW()"
        )


# --- Settings ---


def get_settings(user_id: int) -> Optional[Dict[str, Any]]:
    """Get user settings. Creates default row if missing."""
    with get_cursor() as cur:
        cur.execute(
            """
            SELECT system_prompt, schedule,
                   tool_search_enabled, tool_email_read_enabled, tool_email_send_enabled,
                   tool_hubspot_enabled, tool_notion_enabled,
                   approval_email_send, approval_hubspot, approval_notion,
                   communication_channel, notification_preferences
            FROM settings WHERE user_id = %s
            """,
            (user_id,),
        )
        row = cur.fetchone()
    if row:
        import json
        return {
            "system_prompt": row[0],
            "schedule": row[1],
            "tool_search_enabled": row[2],
            "tool_email_read_enabled": row[3],
            "tool_email_send_enabled": row[4],
            "tool_hubspot_enabled": row[5],
            "tool_notion_enabled": row[6],
            "approval_email_send": row[7],
            "approval_hubspot": row[8],
            "approval_notion": row[9],
            "communication_channel": row[10],
            "notification_preferences": json.loads(row[11]) if row[11] else {},
        }
    return None


def upsert_settings(user_id: int, **kwargs: Any) -> None:
    """Update or insert user settings. Only provided keys are updated."""
    current = get_settings(user_id)
    defaults = {
        "system_prompt": None,
        "schedule": "manual",
        "tool_search_enabled": True,
        "tool_email_read_enabled": True,
        "tool_email_send_enabled": True,
        "tool_hubspot_enabled": True,
        "tool_notion_enabled": True,
        "approval_email_send": True,
        "approval_hubspot": True,
        "approval_notion": True,
        "communication_channel": "telegram",
        "notification_preferences": {},
    }
    merged = {**defaults, **(current or {}), **{k: v for k, v in kwargs.items() if v is not None}}
    with get_cursor() as cur:
        cur.execute(
            """
            INSERT INTO settings (user_id, system_prompt, schedule,
                tool_search_enabled, tool_email_read_enabled, tool_email_send_enabled,
                tool_hubspot_enabled, tool_notion_enabled,
                approval_email_send, approval_hubspot, approval_notion,
                communication_channel, notification_preferences)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE SET
                system_prompt = EXCLUDED.system_prompt,
                schedule = EXCLUDED.schedule,
                tool_search_enabled = EXCLUDED.tool_search_enabled,
                tool_email_read_enabled = EXCLUDED.tool_email_read_enabled,
                tool_email_send_enabled = EXCLUDED.tool_email_send_enabled,
                tool_hubspot_enabled = EXCLUDED.tool_hubspot_enabled,
                tool_notion_enabled = EXCLUDED.tool_notion_enabled,
                approval_email_send = EXCLUDED.approval_email_send,
                approval_hubspot = EXCLUDED.approval_hubspot,
                approval_notion = EXCLUDED.approval_notion,
                communication_channel = EXCLUDED.communication_channel,
                notification_preferences = EXCLUDED.notification_preferences,
                updated_at = NOW()
            """,
            (
                user_id,
                merged.get("system_prompt"),
                merged.get("schedule"),
                merged.get("tool_search_enabled"),
                merged.get("tool_email_read_enabled"),
                merged.get("tool_email_send_enabled"),
                merged.get("tool_hubspot_enabled"),
                merged.get("tool_notion_enabled"),
                merged.get("approval_email_send"),
                merged.get("approval_hubspot"),
                merged.get("approval_notion"),
                merged.get("communication_channel"),
                __json(merged.get("notification_preferences")),
            ),
        )


def __json(obj: Any) -> str:
    import json
    return json.dumps(obj) if obj is not None else "{}"
