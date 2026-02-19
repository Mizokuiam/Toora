"""
worker/publisher.py — Redis pub/sub helpers used by the worker to broadcast status updates.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict

import redis

log = logging.getLogger(__name__)

REDIS_WS_CHANNEL = "toora:ws"
REDIS_STATUS_KEY = "toora:agent_status"


def publish_status(redis_url: str, run_id: int, status: str, extra: Dict[str, Any] | None = None) -> None:
    """Publish agent status to Redis channel (sync version for worker)."""
    try:
        r = redis.from_url(redis_url, decode_responses=True)
        payload = {"type": "agent_status", "data": {"run_id": run_id, "status": status, **(extra or {})}}
        r.publish(REDIS_WS_CHANNEL, json.dumps(payload))
        r.set(REDIS_STATUS_KEY, json.dumps({"run_id": run_id, "status": status}))
        r.close()
    except Exception as exc:
        log.error("publish_status failed: %s", exc)
