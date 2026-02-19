"""
core/config.py — centralised environment variable loading and startup validation.
All services import Settings from here. Raises at import time if required vars are missing.
"""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass
from typing import Optional


@dataclass
class Settings:
    # LLM
    openrouter_api_key: str
    # Database
    database_url: str
    # Redis
    redis_url: str
    # Encryption
    encryption_key: str
    # Service URLs
    backend_url: str
    frontend_url: str
    # Telegram
    telegram_webhook_secret: Optional[str]
    # Next.js (read by Next.js at build time via NEXT_PUBLIC_*)
    next_public_api_url: Optional[str]


def _require(key: str) -> str:
    value = os.environ.get(key, "").strip()
    if not value:
        raise ValueError(key)
    return value


def _optional(key: str) -> Optional[str]:
    return os.environ.get(key, "").strip() or None


def load_settings(required: list[str] | None = None) -> Settings:
    """
    Load settings from environment variables.
    Pass a subset of required keys to only validate those (useful for services
    that only need a subset of all variables).
    """
    _required_defaults = [
        "OPENROUTER_API_KEY",
        "DATABASE_URL",
        "REDIS_URL",
        "ENCRYPTION_KEY",
        "BACKEND_URL",
        "FRONTEND_URL",
    ]
    required = required or _required_defaults
    missing: list[str] = []
    for key in required:
        if not os.environ.get(key, "").strip():
            missing.append(key)
    if missing:
        print(
            f"\n[Toora] Missing required environment variables:\n"
            + "\n".join(f"  - {k}" for k in missing)
            + "\nSet them and restart the service.\n",
            file=sys.stderr,
        )
        sys.exit(1)
    return Settings(
        openrouter_api_key=os.environ.get("OPENROUTER_API_KEY", ""),
        database_url=os.environ.get("DATABASE_URL", ""),
        redis_url=os.environ.get("REDIS_URL", ""),
        encryption_key=os.environ.get("ENCRYPTION_KEY", ""),
        backend_url=os.environ.get("BACKEND_URL", ""),
        frontend_url=os.environ.get("FRONTEND_URL", ""),
        telegram_webhook_secret=_optional("TELEGRAM_WEBHOOK_SECRET"),
        next_public_api_url=_optional("NEXT_PUBLIC_API_URL"),
    )


# Convenience: module-level singleton loaded lazily per service
_settings: Optional[Settings] = None


def get_settings(required: list[str] | None = None) -> Settings:
    global _settings
    if _settings is None:
        _settings = load_settings(required)
    return _settings
