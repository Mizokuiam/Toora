"""
agent/integrations/openrouter.py — OpenRouter LLM API key integration.
Credentials: {"api_key": "..."}
"""

from __future__ import annotations

from typing import Dict

import httpx


async def test_connection(creds: Dict[str, str]) -> str:
    """Validate API key by listing models."""
    api_key = creds.get("api_key", "").strip()
    if not api_key:
        raise RuntimeError("OpenRouter API key is required.")
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            "https://openrouter.ai/api/v1/models",
            headers={"Authorization": f"Bearer {api_key}"},
        )
    if r.status_code == 401:
        raise RuntimeError("Invalid API key. Get one at openrouter.ai/keys.")
    if not r.is_success:
        raise RuntimeError(f"OpenRouter returned {r.status_code}: {r.text[:200]}")
    return "OpenRouter connection successful."
