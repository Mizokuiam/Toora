"""add memory column to agent_config

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-19

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("agent_config", sa.Column("memory", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("agent_config", "memory")
