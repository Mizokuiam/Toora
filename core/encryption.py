"""
Fernet symmetric encryption for storing credentials in PostgreSQL.
Encryption key must be in ENCRYPTION_KEY env var; never stored in DB or code.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict

from cryptography.fernet import Fernet, InvalidToken

from core.config import require_env


def _get_fernet() -> Fernet:
    """Build Fernet from ENCRYPTION_KEY. Use Fernet.generate_key() to create a key."""
    key = require_env("ENCRYPTION_KEY").strip()
    return Fernet(key.encode("utf-8") if isinstance(key, str) else key)


def encrypt_value(plain: str | Dict[str, Any]) -> bytes:
    """
    Encrypt a string or JSON-serializable dict. Returns bytes for BYTEA storage.
    Never log or print the plain value.
    """
    if isinstance(plain, dict):
        plain = json.dumps(plain)
    else:
        plain = str(plain)
    f = _get_fernet()
    return f.encrypt(plain.encode("utf-8"))


def decrypt_value(encrypted: bytes) -> str:
    """Decrypt bytes from DB to plain string. Raises on invalid token."""
    f = _get_fernet()
    return f.decrypt(encrypted).decode("utf-8")


def decrypt_json(encrypted: bytes) -> Dict[str, Any]:
    """Decrypt and parse as JSON dict."""
    return json.loads(decrypt_value(encrypted))
