"""
backend/schemas.py — Pydantic request/response models for all API routes.
All route handlers import from here; no raw dicts cross the API boundary.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Integrations ──────────────────────────────────────────────────────────────

class IntegrationOut(BaseModel):
    id: int
    platform: str
    status: str
    connected_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class CredentialSaveRequest(BaseModel):
    credentials: Dict[str, str] = Field(..., description="Plain-text credential fields")


class TestConnectionResult(BaseModel):
    success: bool
    message: str


# ── Agent ─────────────────────────────────────────────────────────────────────

class AgentRunOut(BaseModel):
    id: int
    triggered_by: str
    triggered_at: datetime
    completed_at: Optional[datetime] = None
    status: str
    summary: Optional[str] = None

    model_config = {"from_attributes": True}


class AgentStatusOut(BaseModel):
    status: str  # running | idle | waiting_for_approval
    run_id: Optional[int] = None
    last_run: Optional[AgentRunOut] = None


class AgentConfigOut(BaseModel):
    enabled_tools: Dict[str, bool]
    schedule: str
    system_prompt: Optional[str] = None
    memory: Optional[str] = None
    approval_rules: Dict[str, bool]

    model_config = {"from_attributes": True}


class AgentConfigUpdate(BaseModel):
    enabled_tools: Optional[Dict[str, bool]] = None
    schedule: Optional[str] = None
    system_prompt: Optional[str] = None
    memory: Optional[str] = None
    approval_rules: Optional[Dict[str, bool]] = None


class AgentRunRequest(BaseModel):
    input: Optional[str] = None


# ── Logs ──────────────────────────────────────────────────────────────────────

class ActionLogOut(BaseModel):
    id: int
    run_id: int
    tool_used: str
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    requires_approval: bool
    approval_status: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class PaginatedLogs(BaseModel):
    items: List[ActionLogOut]
    total: int
    page: int
    per_page: int


# ── Approvals ─────────────────────────────────────────────────────────────────

class ApprovalOut(BaseModel):
    id: int
    run_id: int
    action_description: str
    full_context: Dict[str, Any]
    telegram_message_id: Optional[int] = None
    status: str
    created_at: datetime
    expires_at: datetime
    resolved_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ── Stats ─────────────────────────────────────────────────────────────────────

class TodayStats(BaseModel):
    emails_processed: int
    tasks_created: int
    approvals_pending: int
    last_run_at: Optional[datetime] = None
