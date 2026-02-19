"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-02-18 00:00:00.000000
"""

from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── users ──────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("settings", postgresql.JSONB(), nullable=True),
    )
    op.create_index("ix_users_id", "users", ["id"])
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # Seed default user (portfolio: single-user app)
    op.execute(
        "INSERT INTO users (email, settings) VALUES ('admin@toora.app', '{}') "
        "ON CONFLICT (email) DO NOTHING"
    )

    # ── integrations ───────────────────────────────────────────────────────
    op.create_table(
        "integrations",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("platform", sa.String(50), nullable=False),
        sa.Column("encrypted_credentials", sa.LargeBinary(), nullable=False),
        sa.Column("connected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="connected"),
    )
    op.create_index("ix_integrations_id", "integrations", ["id"])
    op.create_index("ix_integrations_platform", "integrations", ["platform"])

    # ── agent_runs ─────────────────────────────────────────────────────────
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("triggered_by", sa.String(50), nullable=False, server_default="manual"),
        sa.Column(
            "triggered_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("summary", sa.Text(), nullable=True),
    )
    op.create_index("ix_agent_runs_id", "agent_runs", ["id"])

    # ── action_log ─────────────────────────────────────────────────────────
    op.create_table(
        "action_log",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=False
        ),
        sa.Column("tool_used", sa.String(100), nullable=False),
        sa.Column("input_data", postgresql.JSONB(), nullable=True),
        sa.Column("output_data", postgresql.JSONB(), nullable=True),
        sa.Column("requires_approval", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("approval_status", sa.String(20), nullable=True),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_action_log_id", "action_log", ["id"])
    op.create_index("ix_action_log_run_id", "action_log", ["run_id"])
    op.create_index("ix_action_log_timestamp", "action_log", ["timestamp"])

    # ── pending_approvals ──────────────────────────────────────────────────
    op.create_table(
        "pending_approvals",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "run_id", sa.Integer(), sa.ForeignKey("agent_runs.id"), nullable=False
        ),
        sa.Column("action_description", sa.Text(), nullable=False),
        sa.Column("full_context", postgresql.JSONB(), nullable=False),
        sa.Column("telegram_message_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_pending_approvals_id", "pending_approvals", ["id"])
    op.create_index("ix_pending_approvals_run_id", "pending_approvals", ["run_id"])
    op.create_index("ix_pending_approvals_status", "pending_approvals", ["status"])

    # ── agent_config ───────────────────────────────────────────────────────
    op.create_table(
        "agent_config",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column(
            "user_id",
            sa.Integer(),
            sa.ForeignKey("users.id"),
            nullable=False,
            unique=True,
        ),
        sa.Column(
            "enabled_tools",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
        sa.Column("schedule", sa.String(20), nullable=False, server_default="manual"),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column(
            "approval_rules",
            postgresql.JSONB(),
            nullable=False,
            server_default="{}",
        ),
    )
    op.create_index("ix_agent_config_id", "agent_config", ["id"])

    # Seed default config for user id=1
    op.execute(
        "INSERT INTO agent_config (user_id, enabled_tools, schedule, approval_rules) "
        "SELECT 1, "
        "'{\"read_gmail\": true, \"search_web\": true, \"read_webpage\": true, "
        "\"send_email\": true, \"create_notion_task\": true, \"log_to_hubspot\": true, "
        "\"send_telegram_message\": true}'::jsonb, "
        "'manual', "
        "'{\"send_email\": true, \"create_notion_task\": false, \"log_to_hubspot\": false}'::jsonb "
        "WHERE EXISTS (SELECT 1 FROM users WHERE id = 1)"
    )


def downgrade() -> None:
    op.drop_table("agent_config")
    op.drop_table("pending_approvals")
    op.drop_table("action_log")
    op.drop_table("agent_runs")
    op.drop_table("integrations")
    op.drop_table("users")
