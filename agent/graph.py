"""
agent/graph.py — LangGraph ReAct agent.
Loads user config, builds the tool-enabled agent, and runs the loop.
Publishes status updates to Redis pub/sub for real-time WebSocket forwarding.
"""

from __future__ import annotations

import asyncio
import json
import os
import logging
from typing import Any, Dict, Optional

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.tools import ALL_TOOLS, set_run_id, set_main_loop
from core.config import get_settings
from db.base import session_context
from db.models import AgentConfig, AgentRun

log = logging.getLogger(__name__)

DEFAULT_USER_ID = 1
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
MODEL = "deepseek/deepseek-chat-v3-0324"


async def _get_user_config() -> Dict[str, Any]:
    async with session_context() as db:
        from sqlalchemy import select
        result = await db.execute(
            select(AgentConfig).where(AgentConfig.user_id == DEFAULT_USER_ID)
        )
        cfg = result.scalar_one_or_none()
        if not cfg:
            return {"enabled_tools": {}, "system_prompt": None, "memory": None, "approval_rules": {}}
        return {
            "enabled_tools": cfg.enabled_tools or {},
            "system_prompt": cfg.system_prompt,
            "memory": cfg.memory,
            "approval_rules": cfg.approval_rules or {},
        }


async def _send_summary_to_telegram(summary: str) -> None:
    """Send agent run summary to Telegram with action menu (BotFather style)."""
    try:
        from agent.approval import _get_telegram_creds
        from agent.integrations.telegram import build_briefing_keyboard, send_message
        creds = await _get_telegram_creds()
        if creds:
            text = f"*🤖 Toora briefing*\n\n{summary[:4000]}"
            frontend_url = os.environ.get("FRONTEND_URL", "https://frontend-production-8833b.up.railway.app")
            await send_message(creds, text, build_briefing_keyboard(frontend_url))
            log.info("Summary sent to Telegram.")
    except Exception as exc:
        log.warning("Failed to send summary to Telegram: %s", exc)


async def _publish_status(redis_url: str, run_id: int, status: str, payload: Optional[Dict] = None) -> None:
    import redis.asyncio as aioredis
    try:
        r = aioredis.from_url(redis_url, decode_responses=True)
        msg = json.dumps({"type": "agent_status", "data": {"status": status, "run_id": run_id, **(payload or {})}})
        await r.publish("toora:ws", msg)
        await r.set("toora:agent_status", json.dumps({"status": status, "run_id": run_id}))
        await r.aclose()
    except Exception as exc:
        log.error("Failed to publish status: %s", exc)


async def run_agent(run_id: int, user_input: str = "Process my inbox and provide a daily briefing.") -> str:
    """Run the LangGraph ReAct agent for the given run_id."""
    settings = get_settings(required=["OPENROUTER_API_KEY", "DATABASE_URL", "REDIS_URL"])
    set_run_id(run_id)
    set_main_loop(asyncio.get_running_loop())

    await _publish_status(settings.redis_url, run_id, "running")

    config = await _get_user_config()

    # Filter tools based on user's enabled_tools setting
    enabled = config.get("enabled_tools", {})
    active_tools = [t for t in ALL_TOOLS if enabled.get(t.name, True)]

    base_prompt = (
        config.get("system_prompt")
        or "You are Toora, an autonomous AI executive assistant for a small business owner. "
           "Process the user's inbox, research relevant topics, and take action where needed. "
           "Always be concise, professional, and proactive."
    )
    memory = (config.get("memory") or "").strip()
    system_prompt = base_prompt
    if memory:
        system_prompt = f"{base_prompt}\n\n**Things to remember about this user:**\n{memory}"

    llm = ChatOpenAI(
        model=MODEL,
        base_url=OPENROUTER_BASE,
        api_key=settings.openrouter_api_key,
        temperature=0.2,
    )

    agent = create_react_agent(llm, active_tools, prompt=system_prompt)

    try:
        result = await agent.ainvoke({"messages": [("user", user_input)]})
        summary = result["messages"][-1].content if result.get("messages") else "Agent run completed."
        await _publish_status(settings.redis_url, run_id, "idle", {"summary": summary[:500]})

        # Send summary to Telegram if connected
        await _send_summary_to_telegram(summary)

        # Update run record
        async with session_context() as db:
            from datetime import datetime, timezone
            from sqlalchemy import select
            r = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
            run = r.scalar_one_or_none()
            if run:
                run.status = "completed"
                run.completed_at = datetime.now(tz=timezone.utc)
                run.summary = summary[:2000]

        return summary
    except Exception as exc:
        log.error("Agent run %d failed: %s", run_id, exc)
        await _publish_status(settings.redis_url, run_id, "idle", {"error": str(exc)})

        async with session_context() as db:
            from datetime import datetime, timezone
            from sqlalchemy import select
            r = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
            run = r.scalar_one_or_none()
            if run:
                run.status = "failed"
                run.completed_at = datetime.now(tz=timezone.utc)
                run.summary = str(exc)[:2000]

        return f"Agent failed: {exc}"
