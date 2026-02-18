"""
Agent tools: each tool logs to action_log and respects approval settings.
Requires approval: send_email (always), create_notion_task, log_to_hubspot (if enabled).
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from db import models as db_models
from integrations import gmail as gmail_int
from integrations import telegram as telegram_int
from integrations import hubspot as hubspot_int
from integrations import notion as notion_int
from integrations import search as search_int


# Approval timeout in seconds
APPROVAL_TIMEOUT_SEC = 600


def _log_action(
    user_id: int,
    run_id: Optional[int],
    tool_used: str,
    input_summary: Optional[str],
    input_full: Optional[Dict],
    output_summary: Optional[str],
    output_full: Optional[Dict],
    status: str = "completed",
    approval_status: Optional[str] = None,
) -> int:
    return db_models.insert_action_log(
        user_id=user_id,
        run_id=run_id,
        tool_used=tool_used,
        input_summary=input_summary,
        input_full=input_full,
        output_summary=output_summary,
        output_full=output_full,
        status=status,
        approval_status=approval_status,
    )


def _require_approval_and_wait(
    user_id: int,
    run_id: Optional[int],
    action_description: str,
    action_type: str,
    action_payload: Dict[str, Any],
    get_telegram_creds: Callable[[], Optional[Dict]],
) -> Optional[bool]:
    """
    Send Telegram approval request, create pending_approval, wait for decision (poll DB + Redis).
    Returns True if approved, False if rejected, None if expired.
    """
    creds = get_telegram_creds()
    if not creds:
        return False
    approval_id = db_models.create_pending_approval(
        user_id=user_id,
        run_id=run_id,
        action_description=action_description,
        action_type=action_type,
        action_payload=action_payload,
        telegram_message_id=None,
        expires_at_sec=APPROVAL_TIMEOUT_SEC,
    )
    text = f"<b>Approval required</b>\n\n{action_description}\n\nApprove or reject below."
    ok, msg_id, err = telegram_int.send_approval_request(creds, text, approval_id)
    # Poll for decision
    import time
    deadline = time.monotonic() + APPROVAL_TIMEOUT_SEC
    try:
        import redis
        import os
        r = redis.from_url(os.environ.get("REDIS_URL", "")) if os.environ.get("REDIS_URL") else None
    except Exception:
        r = None
    while time.monotonic() < deadline:
        pa = db_models.get_pending_approval(approval_id)
        if not pa:
            break
        if pa["status"] == "approved":
            return True
        if pa["status"] == "rejected":
            return False
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        exp = pa.get("expires_at")
        if exp and (exp.replace(tzinfo=timezone.utc) if exp.tzinfo is None else exp) <= now:
            db_models.set_approval_decision(approval_id, False)
            return None
        # Optional: subscribe to Redis pubsub for faster wake
        if r:
            try:
                pub = r.pubsub()
                pub.subscribe("toora:approvals")
                msg = pub.get_message(timeout=2)
                if msg and msg.get("type") == "message":
                    data = json.loads(msg["data"])
                    if data.get("approval_id") == approval_id:
                        return data.get("approved", False)
                pub.unsubscribe("toora:approvals")
            except Exception:
                pass
        time.sleep(2)
    db_models.expire_old_approvals()
    return None


def read_gmail(user_id: int, run_id: Optional[int], limit: int = 20) -> Dict[str, Any]:
    """Read unread Gmail. Logs and returns list of emails."""
    creds = db_models.get_decrypted_credentials(user_id, "gmail")
    if not creds:
        _log_action(user_id, run_id, "read_gmail", "No credentials", None, "Skipped", None, status="skipped")
        return {"error": "Gmail not connected", "emails": []}
    try:
        emails = gmail_int.read_unread_emails(creds, limit=limit)
        summary = f"Read {len(emails)} unread emails"
        _log_action(user_id, run_id, "read_gmail", summary, {"limit": limit}, summary, {"count": len(emails), "subjects": [e.get("subject") for e in emails]})
        return {"emails": emails, "count": len(emails)}
    except Exception as e:
        _log_action(user_id, run_id, "read_gmail", f"Limit {limit}", {"limit": limit}, str(e), None, status="error")
        return {"error": str(e), "emails": []}


def send_email(
    user_id: int,
    run_id: Optional[int],
    to: str,
    subject: str,
    body: str,
    require_approval: bool = True,
) -> Dict[str, Any]:
    """Send email. Always requires Telegram approval unless disabled in settings."""
    creds = db_models.get_decrypted_credentials(user_id, "gmail")
    if not creds:
        _log_action(user_id, run_id, "send_email", "No credentials", None, "Skipped", None, status="skipped")
        return {"error": "Gmail not connected"}
    if require_approval:
        desc = f"Send email to {to}\nSubject: {subject}\n\nBody:\n{body[:500]}"
        decision = _require_approval_and_wait(
            user_id, run_id, desc, "send_email", {"to": to, "subject": subject, "body": body},
            lambda: db_models.get_decrypted_credentials(user_id, "telegram"),
        )
        if decision is False:
            _log_action(user_id, run_id, "send_email", subject, {"to": to, "subject": subject}, "Rejected", None, status="rejected", approval_status="rejected")
            return {"status": "rejected"}
        if decision is None:
            _log_action(user_id, run_id, "send_email", subject, {"to": to, "subject": subject}, "Expired", None, status="expired", approval_status="expired")
            return {"status": "expired"}
    ok, msg = gmail_int.send_email(creds, to, subject, body)
    if ok:
        _log_action(user_id, run_id, "send_email", subject, {"to": to, "subject": subject}, "Sent", {"ok": True}, approval_status="approved" if require_approval else None)
        return {"status": "sent"}
    _log_action(user_id, run_id, "send_email", subject, {"to": to, "subject": subject}, msg, None, status="error")
    return {"error": msg}


def search_web(user_id: int, run_id: Optional[int], query: str, max_results: int = 5) -> Dict[str, Any]:
    """Web search. No approval needed."""
    try:
        results = search_int.search_web(query, max_results=max_results)
        if results and "error" in results[0]:
            _log_action(user_id, run_id, "search_web", query, {"query": query}, results[0]["error"], None, status="error")
            return results[0]
        summary = f"Found {len(results)} results"
        _log_action(user_id, run_id, "search_web", query, {"query": query}, summary, {"results": results})
        return {"results": results}
    except Exception as e:
        _log_action(user_id, run_id, "search_web", query, {"query": query}, str(e), None, status="error")
        return {"error": str(e)}


def read_webpage(user_id: int, run_id: Optional[int], url: str) -> Dict[str, Any]:
    """Extract article text from URL."""
    try:
        text = search_int.read_webpage(url)
        summary = text[:200] + "..." if len(text) > 200 else text
        _log_action(user_id, run_id, "read_webpage", url, {"url": url}, summary, {"length": len(text)})
        return {"text": text, "url": url}
    except Exception as e:
        _log_action(user_id, run_id, "read_webpage", url, {"url": url}, str(e), None, status="error")
        return {"error": str(e)}


def create_notion_task(
    user_id: int,
    run_id: Optional[int],
    database_id: str,
    title: str,
    require_approval: bool,
) -> Dict[str, Any]:
    """Create a Notion page/task. Optionally requires approval."""
    creds = db_models.get_decrypted_credentials(user_id, "notion")
    if not creds:
        _log_action(user_id, run_id, "create_notion_task", "No credentials", None, "Skipped", None, status="skipped")
        return {"error": "Notion not connected"}
    if require_approval:
        desc = f"Create Notion task in database {database_id}: {title}"
        decision = _require_approval_and_wait(
            user_id, run_id, desc, "create_notion_task", {"database_id": database_id, "title": title},
            lambda: db_models.get_decrypted_credentials(user_id, "telegram"),
        )
        if decision is False:
            _log_action(user_id, run_id, "create_notion_task", title, {"database_id": database_id, "title": title}, "Rejected", None, status="rejected", approval_status="rejected")
            return {"status": "rejected"}
        if decision is None:
            _log_action(user_id, run_id, "create_notion_task", title, {"database_id": database_id, "title": title}, "Expired", None, status="expired", approval_status="expired")
            return {"status": "expired"}
    page_id = notion_int.create_page_in_database(creds, database_id, title)
    if page_id:
        _log_action(user_id, run_id, "create_notion_task", title, {"database_id": database_id, "title": title}, f"Created page {page_id}", {"page_id": page_id}, approval_status="approved" if require_approval else None)
        return {"page_id": page_id, "status": "created"}
    _log_action(user_id, run_id, "create_notion_task", title, {"database_id": database_id, "title": title}, "API error", None, status="error")
    return {"error": "Failed to create page"}


def log_to_hubspot(
    user_id: int,
    run_id: Optional[int],
    email: str,
    note: str,
    properties: Optional[Dict[str, str]] = None,
    require_approval: bool = True,
) -> Dict[str, Any]:
    """Create/update HubSpot contact and log note. Optionally requires approval."""
    creds = db_models.get_decrypted_credentials(user_id, "hubspot")
    if not creds:
        _log_action(user_id, run_id, "log_to_hubspot", "No credentials", None, "Skipped", None, status="skipped")
        return {"error": "HubSpot not connected"}
    if require_approval:
        desc = f"HubSpot: add/update contact {email} with note: {note[:200]}"
        decision = _require_approval_and_wait(
            user_id, run_id, desc, "log_to_hubspot", {"email": email, "note": note, "properties": properties or {}},
            lambda: db_models.get_decrypted_credentials(user_id, "telegram"),
        )
        if decision is False:
            _log_action(user_id, run_id, "log_to_hubspot", email, {"email": email, "note": note}, "Rejected", None, status="rejected", approval_status="rejected")
            return {"status": "rejected"}
        if decision is None:
            _log_action(user_id, run_id, "log_to_hubspot", email, {"email": email, "note": note}, "Expired", None, status="expired", approval_status="expired")
            return {"status": "expired"}
    contact_id = hubspot_int.create_or_update_contact(creds, email, properties)
    if contact_id:
        note_id = hubspot_int.log_activity_note(creds, contact_id, note)
        _log_action(user_id, run_id, "log_to_hubspot", email, {"email": email, "note": note}, f"Contact {contact_id}, note {note_id}", {"contact_id": contact_id, "note_id": note_id}, approval_status="approved" if require_approval else None)
        return {"contact_id": contact_id, "note_id": note_id, "status": "ok"}
    _log_action(user_id, run_id, "log_to_hubspot", email, {"email": email, "note": note}, "API error", None, status="error")
    return {"error": "Failed to create/update contact"}


def send_telegram_message(user_id: int, run_id: Optional[int], text: str) -> Dict[str, Any]:
    """Send a message to the user's Telegram. No approval needed."""
    creds = db_models.get_decrypted_credentials(user_id, "telegram")
    if not creds:
        _log_action(user_id, run_id, "send_telegram_message", "No credentials", None, "Skipped", None, status="skipped")
        return {"error": "Telegram not connected"}
    ok, msg_id, err = telegram_int.send_message(creds, text)
    if ok:
        _log_action(user_id, run_id, "send_telegram_message", text[:100], {"text": text}, f"Sent message_id={msg_id}", {"message_id": msg_id})
        return {"message_id": msg_id, "status": "sent"}
    _log_action(user_id, run_id, "send_telegram_message", text[:100], {"text": text}, err, None, status="error")
    return {"error": err}
