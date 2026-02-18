"""
SQL migrations for Toora PostgreSQL schema.
Creates users, credentials, agent runs, action log, pending approvals, and settings.
All tables use parameterized queries via the connection module.
"""

from __future__ import annotations

from db.connection import get_cursor


def run_migrations() -> None:
    """Create all tables if they do not exist."""
    with get_cursor() as cur:
        # Users: single-tenant for portfolio; can extend to multi-user later
        cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                external_id VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Encrypted credentials per integration (one row per user per integration)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS credentials (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                integration VARCHAR(64) NOT NULL,
                encrypted_payload BYTEA NOT NULL,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW(),
                UNIQUE(user_id, integration)
            );
        """)

        # Agent runs: each time the agent is triggered
        cur.execute("""
            CREATE TABLE IF NOT EXISTS agent_runs (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                triggered_at TIMESTAMPTZ DEFAULT NOW(),
                status VARCHAR(32) NOT NULL DEFAULT 'running',
                summary TEXT,
                finished_at TIMESTAMPTZ,
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Action log: every tool execution
        cur.execute("""
            CREATE TABLE IF NOT EXISTS action_log (
                id SERIAL PRIMARY KEY,
                run_id INTEGER REFERENCES agent_runs(id) ON DELETE SET NULL,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                tool_used VARCHAR(64) NOT NULL,
                input_summary TEXT,
                input_full JSONB,
                output_summary TEXT,
                output_full JSONB,
                status VARCHAR(32) NOT NULL DEFAULT 'pending',
                approval_status VARCHAR(32),
                created_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Pending approvals: actions waiting for user (Telegram or dashboard)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS pending_approvals (
                id SERIAL PRIMARY KEY,
                run_id INTEGER REFERENCES agent_runs(id) ON DELETE SET NULL,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                action_description TEXT NOT NULL,
                action_type VARCHAR(64) NOT NULL,
                action_payload JSONB NOT NULL,
                telegram_message_id BIGINT,
                status VARCHAR(32) NOT NULL DEFAULT 'pending',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                expires_at TIMESTAMPTZ NOT NULL
            );
        """)

        # Settings: user preferences, enabled tools, schedule, system prompt, approval toggles
        cur.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE UNIQUE,
                system_prompt TEXT,
                schedule VARCHAR(32) NOT NULL DEFAULT 'manual',
                tool_search_enabled BOOLEAN DEFAULT TRUE,
                tool_email_read_enabled BOOLEAN DEFAULT TRUE,
                tool_email_send_enabled BOOLEAN DEFAULT TRUE,
                tool_hubspot_enabled BOOLEAN DEFAULT TRUE,
                tool_notion_enabled BOOLEAN DEFAULT TRUE,
                approval_email_send BOOLEAN DEFAULT TRUE,
                approval_hubspot BOOLEAN DEFAULT TRUE,
                approval_notion BOOLEAN DEFAULT TRUE,
                communication_channel VARCHAR(32) DEFAULT 'telegram',
                notification_preferences JSONB DEFAULT '{}',
                created_at TIMESTAMPTZ DEFAULT NOW(),
                updated_at TIMESTAMPTZ DEFAULT NOW()
            );
        """)

        # Indexes for common queries
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_runs_user_triggered
            ON agent_runs(user_id, triggered_at DESC);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_log_run_id
            ON action_log(run_id);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_action_log_created
            ON action_log(created_at DESC);
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_pending_approvals_status_expires
            ON pending_approvals(status, expires_at);
        """)
