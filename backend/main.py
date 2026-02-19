"""
backend/main.py — FastAPI application entry point.
Mounts all routers, configures CORS, exposes the WebSocket endpoint,
and validates required environment variables at startup.
"""

from __future__ import annotations

import logging
import sys
import os

# Ensure repo root is in path so 'core', 'db', 'backend' packages are found.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from core.config import get_settings
from backend.routers import agent, approvals, integrations, logs, stats
from backend.ws.manager import ws_manager

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings(
        required=["DATABASE_URL", "REDIS_URL", "ENCRYPTION_KEY", "FRONTEND_URL"]
    )
    app.state.redis_url = settings.redis_url
    ws_manager.init_redis(settings.redis_url)
    await ws_manager.start_pubsub_listener()
    log.info("Toora backend started.")
    yield
    await ws_manager.stop()
    log.info("Toora backend stopped.")


app = FastAPI(title="Toora API", version="2.0.0", lifespan=lifespan)

# CORS — allow the frontend Railway domain (and localhost for dev)
_settings = get_settings.__wrapped__ if hasattr(get_settings, "__wrapped__") else None
_frontend_url = os.environ.get("FRONTEND_URL", "http://localhost:3000")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[_frontend_url, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(integrations.router)
app.include_router(agent.router)
app.include_router(logs.router)
app.include_router(approvals.router)
app.include_router(stats.router)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.websocket("/ws/agent")
async def websocket_endpoint(ws: WebSocket):
    await ws_manager.connect(ws)
    try:
        while True:
            # Keep alive — client can send pings; we ignore them
            await ws.receive_text()
    except WebSocketDisconnect:
        await ws_manager.disconnect(ws)
