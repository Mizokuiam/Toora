"""
worker/main.py — Redis queue consumer and LangGraph agent dispatcher.
Infinite loop: BLPOP toora:agent_jobs → create AgentRun → run agent.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

import redis

# Ensure repo root is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from core.config import get_settings
from db.base import session_context
from db.models import AgentRun
from worker.publisher import publish_status

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
log = logging.getLogger("worker")

REDIS_JOB_QUEUE = "toora:agent_jobs"


async def _create_run(user_id: int, triggered_by: str) -> int:
    """Insert an AgentRun row and return its id."""
    async with session_context() as db:
        run = AgentRun(
            user_id=user_id,
            triggered_by=triggered_by,
            triggered_at=datetime.now(tz=timezone.utc),
            status="running",
        )
        db.add(run)
        await db.flush()
        run_id = run.id
    return run_id


async def process_job(job: dict, redis_url: str) -> None:
    user_id = job.get("user_id", 1)
    triggered_by = job.get("triggered_by", "manual")
    user_input = job.get("input", "Process my inbox and provide a daily briefing.")

    log.info("Processing job: user_id=%s, triggered_by=%s", user_id, triggered_by)
    run_id = await _create_run(user_id, triggered_by)
    publish_status(redis_url, run_id, "running")

    try:
        from agent.graph import run_agent
        summary = await run_agent(run_id, user_input)
        log.info("Run %d completed: %s", run_id, summary[:100])
    except Exception as exc:
        log.error("Run %d failed: %s", run_id, exc)
        publish_status(redis_url, run_id, "idle", {"error": str(exc)})


def main() -> None:
    settings = get_settings(
        required=["DATABASE_URL", "REDIS_URL", "ENCRYPTION_KEY", "OPENROUTER_API_KEY"]
    )
    log.info("Toora worker started. Listening on queue: %s", REDIS_JOB_QUEUE)

    r = redis.from_url(settings.redis_url, decode_responses=True)

    while True:
        try:
            result = r.blpop(REDIS_JOB_QUEUE, timeout=30)
            if result is None:
                continue
            _, raw = result
            job = json.loads(raw)
            asyncio.run(process_job(job, settings.redis_url))
        except redis.exceptions.ConnectionError as exc:
            log.error("Redis connection error: %s — retrying in 5s", exc)
            import time
            time.sleep(5)
        except Exception as exc:
            log.error("Unexpected error in worker loop: %s", exc, exc_info=True)


if __name__ == "__main__":
    main()
