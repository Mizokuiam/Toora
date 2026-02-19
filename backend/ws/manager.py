"""
backend/ws/manager.py — WebSocket connection manager.
Maintains active connections, subscribes to Redis pub/sub, and fans out messages
to all connected dashboard clients.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any, Dict, Set

import redis.asyncio as aioredis
from fastapi import WebSocket

log = logging.getLogger(__name__)

REDIS_WS_CHANNEL = "toora:ws"


class WebSocketManager:
    def __init__(self) -> None:
        self._connections: Set[WebSocket] = set()
        self._redis: aioredis.Redis | None = None
        self._listener_task: asyncio.Task | None = None

    def init_redis(self, redis_url: str) -> None:
        self._redis = aioredis.from_url(redis_url, decode_responses=True)

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.add(ws)
        log.info("WS client connected (total=%d)", len(self._connections))

    async def disconnect(self, ws: WebSocket) -> None:
        self._connections.discard(ws)
        log.info("WS client disconnected (total=%d)", len(self._connections))

    async def broadcast(self, payload: Dict[str, Any]) -> None:
        dead: list[WebSocket] = []
        text = json.dumps(payload)
        for ws in list(self._connections):
            try:
                await ws.send_text(text)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self._connections.discard(ws)

    async def start_pubsub_listener(self) -> None:
        """Subscribe to Redis channel and fan out messages to all WS clients."""
        if self._redis is None:
            log.warning("Redis not initialised; WS pub/sub listener not started.")
            return
        self._listener_task = asyncio.create_task(self._listen())

    async def _listen(self) -> None:
        assert self._redis is not None
        pubsub = self._redis.pubsub()
        await pubsub.subscribe(REDIS_WS_CHANNEL)
        log.info("Subscribed to Redis channel: %s", REDIS_WS_CHANNEL)
        async for message in pubsub.listen():
            if message["type"] == "message":
                try:
                    payload = json.loads(message["data"])
                    await self.broadcast(payload)
                except Exception as exc:
                    log.error("Failed to broadcast WS message: %s", exc)

    async def stop(self) -> None:
        if self._listener_task:
            self._listener_task.cancel()
        if self._redis:
            await self._redis.aclose()


ws_manager = WebSocketManager()
