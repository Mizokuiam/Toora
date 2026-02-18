"""
Database package: models, migrations, and query helpers for Toora.
Uses PostgreSQL with parameterized queries and encrypted credential storage.
"""

from db.connection import get_connection, init_db
from db.models import (
    get_or_create_user,
    save_credentials,
    get_decrypted_credentials,
)

__all__ = [
    "get_connection",
    "init_db",
    "get_or_create_user",
    "save_credentials",
    "get_decrypted_credentials",
]
