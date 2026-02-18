"""
Configuration and environment variable loading.
Never logs or prints secrets.
"""

from __future__ import annotations

import os
from typing import Optional


def get_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable. Returns default if unset."""
    return os.environ.get(key, default)


def require_env(key: str) -> str:
    """Get required environment variable. Raises if unset."""
    value = os.environ.get(key)
    if not value:
        raise ValueError(f"Required environment variable {key} is not set")
    return value
