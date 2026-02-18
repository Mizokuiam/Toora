"""
Redis queue: push agent jobs from dashboard; worker consumes here.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

QUEUE_KEY = "toora:agent_jobs"


def get_redis():
    """Lazy Redis connection from REDIS_URL."""
    import redis
    url = os.environ.get("REDIS_URL")
    if not url:
        raise ValueError("REDIS_URL not set")
    return redis.from_url(url)


def push_agent_job(user_id: int, payload: Optional[Dict[str, Any]] = None) -> None:
    """Push a job for the agent worker. Payload can include run_id, etc."""
    r = get_redis()
    job = {"user_id": user_id, **(payload or {})}
    r.rpush(QUEUE_KEY, json.dumps(job))


def pop_agent_job(timeout_sec: int = 30):
    """Block and pop one job. Returns parsed dict or None."""
    import redis
    url = os.environ.get("REDIS_URL")
    if not url:
        return None
    r = redis.from_url(url)
    result = r.blpop(QUEUE_KEY, timeout=timeout_sec)
    if not result:
        return None
    _, data = result
    return json.loads(data)
