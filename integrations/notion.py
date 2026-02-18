"""
Notion API: create pages/tasks in a user-specified database.
Credentials: api_key. Database ID passed per call. Never logs API key.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

BASE = "https://api.notion.com/v1"


def test_connection(creds: Dict[str, Any]) -> tuple[bool, str]:
    """Test API key with a minimal request. creds: api_key."""
    try:
        r = requests.get(
            f"{BASE}/users/me",
            headers={"Authorization": f"Bearer {creds['api_key']}", "Notion-Version": "2022-06-28"},
            timeout=10,
        )
        if r.status_code == 200:
            return True, "Connected successfully"
        return False, r.text or f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


def create_page_in_database(
    creds: Dict[str, Any],
    database_id: str,
    title: str,
    properties: Optional[Dict[str, Any]] = None,
) -> Optional[str]:
    """
    Create a page in the given database. Title mapped to first title property if needed.
    Returns page id.
    """
    api_key = creds["api_key"]
    headers = {"Authorization": f"Bearer {api_key}", "Notion-Version": "2022-06-28", "Content-Type": "application/json"}
    # Notion title property is usually "title" or "Name"
    props = properties or {}
    if "title" not in props and "Name" not in props:
        props["title"] = {"title": [{"text": {"content": title}}]}
    payload: Dict[str, Any] = {"parent": {"database_id": database_id}, "properties": props}
    if "title" in props and isinstance(props["title"], str):
        payload["properties"]["title"] = {"title": [{"text": {"content": props["title"]}}]}
    elif "title" in props and isinstance(props["title"], dict) and "title" in props["title"]:
        pass
    else:
        payload["properties"]["title"] = {"title": [{"text": {"content": title}}]}
    r = requests.post(f"{BASE}/pages", headers=headers, json=payload, timeout=10)
    if r.status_code in (200, 201):
        return r.json().get("id")
    return None
