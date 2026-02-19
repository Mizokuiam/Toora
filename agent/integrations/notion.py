"""
agent/integrations/notion.py — Notion API integration for task creation.
Credentials: {"api_key": "...", "database_id": "..."}
"""

from __future__ import annotations

from typing import Any, Dict

import httpx

_BASE = "https://api.notion.com/v1"
_NOTION_VERSION = "2022-06-28"


def _headers(creds: Dict[str, str]) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {creds['api_key']}",
        "Notion-Version": _NOTION_VERSION,
        "Content-Type": "application/json",
    }


async def test_connection(creds: Dict[str, str]) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{_BASE}/databases/{creds['database_id']}",
            headers=_headers(creds),
        )
        r.raise_for_status()
        data = r.json()
        title = data.get("title", [{}])[0].get("plain_text", "Untitled")
        return f"Notion connected — database: {title}"


async def create_task(
    creds: Dict[str, str], title: str, content: str = ""
) -> Dict[str, Any]:
    payload = {
        "parent": {"database_id": creds["database_id"]},
        "properties": {
            "Name": {"title": [{"text": {"content": title}}]},
        },
    }
    if content:
        payload["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": [{"type": "text", "text": {"content": content}}]},
            }
        ]
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(f"{_BASE}/pages", headers=_headers(creds), json=payload)
        r.raise_for_status()
        return r.json()
