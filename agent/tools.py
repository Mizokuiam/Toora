"""
agent/tools.py — LangGraph tool implementations for all 7 agent tools.
Each tool: decrypts credentials, executes the integration, logs to action_log,
checks approval rules before consequential actions.
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from langchain_core.tools import tool

from core.encryption import decrypt_dict
from db.base import session_context
from db.models import ActionLog, AgentConfig, Integration

log = logging.getLogger(__name__)

DEFAULT_USER_ID = 1

# Shared run_id set by the worker before running the agent
_current_run_id: int = 0


def set_run_id(run_id: int) -> None:
    global _current_run_id
    _current_run_id = run_id


async def _get_creds(platform: str) -> Optional[Dict[str, str]]:
    async with session_context() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(Integration).where(
                Integration.user_id == DEFAULT_USER_ID,
                Integration.platform == platform,
                Integration.status == "connected",
            )
        )
        row = result.scalar_one_or_none()
        if not row:
            return None
        return decrypt_dict(row.encrypted_credentials)


async def _get_approval_rules() -> Dict[str, bool]:
    async with session_context() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(AgentConfig).where(AgentConfig.user_id == DEFAULT_USER_ID)
        )
        cfg = result.scalar_one_or_none()
        return cfg.approval_rules if cfg else {}


async def _log_action(
    tool_name: str,
    input_data: Dict[str, Any],
    output_data: Dict[str, Any],
    requires_approval: bool = False,
    approval_status: Optional[str] = None,
) -> None:
    async with session_context() as db:
        entry = ActionLog(
            run_id=_current_run_id,
            tool_used=tool_name,
            input_data=input_data,
            output_data=output_data,
            requires_approval=requires_approval,
            approval_status=approval_status,
            timestamp=datetime.now(tz=timezone.utc),
        )
        db.add(entry)


def _run(coro):
    """Run coroutine from a sync context (LangChain tool interface)."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool
def read_gmail(max_count: int = 10) -> str:
    """Read unread emails from Gmail. Returns a JSON list of emails."""
    async def _impl():
        creds = await _get_creds("gmail")
        if not creds:
            return json.dumps({"error": "Gmail not configured."})
        from agent.integrations.gmail import read_unread_emails
        emails = read_unread_emails(creds, max_count)
        await _log_action("read_gmail", {"max_count": max_count}, {"count": len(emails), "emails": emails})
        return json.dumps(emails)
    return _run(_impl())


@tool
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email via Gmail SMTP. ALWAYS requires Telegram approval first."""
    async def _impl():
        from agent.approval import require_approval
        decision = await require_approval(
            run_id=_current_run_id,
            action_description=f"Send email to {to}: {subject}",
            full_context={"to": to, "subject": subject, "body_preview": body[:300]},
        )
        status = "approved" if decision is True else "rejected" if decision is False else "expired"
        if decision:
            creds = await _get_creds("gmail")
            if not creds:
                await _log_action("send_email", {"to": to, "subject": subject}, {"error": "Gmail not configured."}, True, status)
                return "Gmail not configured."
            from agent.integrations.gmail import send_email_smtp
            send_email_smtp(creds, to, subject, body)
            await _log_action("send_email", {"to": to, "subject": subject}, {"sent": True}, True, status)
            return f"Email sent to {to}."
        await _log_action("send_email", {"to": to, "subject": subject}, {"sent": False}, True, status)
        return f"Email not sent — decision: {status}."
    return _run(_impl())


@tool
def search_web(query: str, max_results: int = 5) -> str:
    """Search the web using DuckDuckGo. Returns top results as JSON."""
    async def _impl():
        from agent.integrations.search import search_web as _search
        results = _search(query, max_results)
        await _log_action("search_web", {"query": query}, {"results": results})
        return json.dumps(results)
    return _run(_impl())


@tool
def read_webpage(url: str) -> str:
    """Fetch and extract clean article text from a URL."""
    async def _impl():
        from agent.integrations.search import read_webpage as _read
        content = _read(url)
        await _log_action("read_webpage", {"url": url}, {"length": len(content or ""), "preview": (content or "")[:300]})
        return content or "No content extracted."
    return _run(_impl())


@tool
def create_notion_task(title: str, content: str = "") -> str:
    """Create a task in the user's Notion database. May require approval."""
    async def _impl():
        rules = await _get_approval_rules()
        requires = rules.get("create_notion_task", False)
        decision = True
        if requires:
            from agent.approval import require_approval
            decision = await require_approval(
                run_id=_current_run_id,
                action_description=f"Create Notion task: {title}",
                full_context={"title": title, "content": content},
            )
        status = "approved" if decision else ("rejected" if decision is False else "expired")
        if decision:
            creds = await _get_creds("notion")
            if not creds:
                await _log_action("create_notion_task", {"title": title}, {"error": "Notion not configured."}, requires, status if requires else None)
                return "Notion not configured."
            from agent.integrations.notion import create_task
            result = await create_task(creds, title, content)
            await _log_action("create_notion_task", {"title": title}, {"page_id": result.get("id")}, requires, status if requires else None)
            return f"Notion task created: {result.get('id')}"
        await _log_action("create_notion_task", {"title": title}, {"created": False}, requires, status)
        return f"Task not created — decision: {status}."
    return _run(_impl())


@tool
def log_to_hubspot(email: str, note: str, properties: str = "{}") -> str:
    """Create/update a HubSpot contact and log an activity note. May require approval."""
    async def _impl():
        rules = await _get_approval_rules()
        requires = rules.get("log_to_hubspot", False)
        decision = True
        if requires:
            from agent.approval import require_approval
            decision = await require_approval(
                run_id=_current_run_id,
                action_description=f"Log to HubSpot: contact {email}",
                full_context={"email": email, "note": note},
            )
        status = "approved" if decision else ("rejected" if decision is False else "expired")
        if decision:
            creds = await _get_creds("hubspot")
            if not creds:
                await _log_action("log_to_hubspot", {"email": email}, {"error": "HubSpot not configured."}, requires, status if requires else None)
                return "HubSpot not configured."
            props = json.loads(properties)
            from agent.integrations.hubspot import log_note, upsert_contact
            contact = await upsert_contact(creds, email, props)
            contact_id = contact.get("id", "")
            if contact_id:
                await log_note(creds, contact_id, note)
            await _log_action("log_to_hubspot", {"email": email, "note": note}, {"contact_id": contact_id}, requires, status if requires else None)
            return f"HubSpot contact {email} updated, note logged."
        await _log_action("log_to_hubspot", {"email": email}, {"logged": False}, requires, status)
        return f"HubSpot not updated — decision: {status}."
    return _run(_impl())


@tool
def send_telegram_message(text: str) -> str:
    """Send a message to the user's Telegram chat. No approval required."""
    async def _impl():
        creds = await _get_creds("telegram")
        if not creds:
            await _log_action("send_telegram_message", {"text": text[:100]}, {"error": "Telegram not configured."})
            return "Telegram not configured."
        from agent.integrations.telegram import send_message
        await send_message(creds, text)
        await _log_action("send_telegram_message", {"text": text[:100]}, {"sent": True})
        return "Telegram message sent."
    return _run(_impl())


ALL_TOOLS = [
    read_gmail,
    send_email,
    search_web,
    read_webpage,
    create_notion_task,
    log_to_hubspot,
    send_telegram_message,
]
