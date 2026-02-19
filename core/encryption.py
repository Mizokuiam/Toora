"""
core/encryption.py — Fernet symmetric encryption for credential storage.
Encryption key must live in ENCRYPTION_KEY env var; never hardcoded or logged.
"""

from __future__ import annotations

import json
from typing import Any, Dict

from cryptography.fernet import Fernet

from core.config import get_settings


def _fernet() -> Fernet:
    key = get_settings(required=["ENCRYPTION_KEY"]).encryption_key.strip()
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt_dict(payload: Dict[str, Any]) -> bytes:
    """Encrypt a JSON-serialisable dict. Returns raw bytes for BYTEA storage."""
    return _fernet().encrypt(json.dumps(payload).encode("utf-8"))


def decrypt_dict(data: bytes) -> Dict[str, Any]:
    """Decrypt bytes from DB and parse as JSON dict."""
    return json.loads(_fernet().decrypt(data).decode("utf-8"))


def encrypt_str(value: str) -> bytes:
    return _fernet().encrypt(value.encode("utf-8"))


def decrypt_str(data: bytes) -> str:
    return _fernet().decrypt(data).decode("utf-8")
