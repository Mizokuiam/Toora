"""
db/models.py — SQLAlchemy ORM models for all six Toora tables.
All credential data is stored encrypted (bytes) in the integrations table.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from db.base import Base


# ── Users ─────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    settings: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)

    integrations: Mapped[list["Integration"]] = relationship(
        "Integration", back_populates="user", cascade="all, delete-orphan"
    )
    agent_runs: Mapped[list["AgentRun"]] = relationship(
        "AgentRun", back_populates="user", cascade="all, delete-orphan"
    )
    agent_config: Mapped[Optional["AgentConfig"]] = relationship(
        "AgentConfig", back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


# ── Integrations ──────────────────────────────────────────────────────────────

class Integration(Base):
    __tablename__ = "integrations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    # platform: gmail | telegram | hubspot | notion
    platform: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    encrypted_credentials: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    connected_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="connected")

    user: Mapped["User"] = relationship("User", back_populates="integrations")


# ── Agent Runs ────────────────────────────────────────────────────────────────

class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    triggered_by: Mapped[str] = mapped_column(
        String(50), nullable=False, default="manual"
    )  # manual | schedule | telegram
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="running"
    )  # running | completed | failed | cancelled
    summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    user: Mapped["User"] = relationship("User", back_populates="agent_runs")
    action_logs: Mapped[list["ActionLog"]] = relationship(
        "ActionLog", back_populates="run", cascade="all, delete-orphan"
    )
    pending_approvals: Mapped[list["PendingApproval"]] = relationship(
        "PendingApproval", back_populates="run", cascade="all, delete-orphan"
    )


# ── Action Log ────────────────────────────────────────────────────────────────

class ActionLog(Base):
    __tablename__ = "action_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agent_runs.id"), nullable=False, index=True
    )
    tool_used: Mapped[str] = mapped_column(String(100), nullable=False)
    input_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    output_data: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    requires_approval: Mapped[bool] = mapped_column(default=False)
    approval_status: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )  # None | pending | approved | rejected | expired
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="action_logs")


# ── Pending Approvals ─────────────────────────────────────────────────────────

class PendingApproval(Base):
    __tablename__ = "pending_approvals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    run_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("agent_runs.id"), nullable=False, index=True
    )
    action_description: Mapped[str] = mapped_column(Text, nullable=False)
    full_context: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False)
    telegram_message_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | approved | rejected | expired
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    run: Mapped["AgentRun"] = relationship("AgentRun", back_populates="pending_approvals")


# ── Agent Config ──────────────────────────────────────────────────────────────

class AgentConfig(Base):
    __tablename__ = "agent_config"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id"), unique=True, nullable=False
    )
    enabled_tools: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )
    schedule: Mapped[str] = mapped_column(
        String(20), nullable=False, default="manual"
    )  # manual | 30min | 1hour | 4hours
    system_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    memory: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    approval_rules: Mapped[Dict[str, Any]] = mapped_column(
        JSONB, nullable=False, default=dict
    )

    user: Mapped["User"] = relationship("User", back_populates="agent_config")
