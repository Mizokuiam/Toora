"""
agent/integrations/hubspot.py — HubSpot Private App API integration.
Credentials: {"private_app_token": "..."}
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import httpx

_BASE = "https://api.hubapi.com"


def _headers(creds: Dict[str, str]) -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {creds['private_app_token']}",
        "Content-Type": "application/json",
    }


async def test_connection(creds: Dict[str, str]) -> str:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(
            f"{_BASE}/crm/v3/objects/contacts",
            headers=_headers(creds),
            params={"limit": 1},
        )
        r.raise_for_status()
        return "HubSpot connection successful."


async def upsert_contact(
    creds: Dict[str, str], email: str, properties: Dict[str, str]
) -> Dict[str, Any]:
    """Create or update a contact by email."""
    async with httpx.AsyncClient(timeout=15) as client:
        search_r = await client.post(
            f"{_BASE}/crm/v3/objects/contacts/search",
            headers=_headers(creds),
            json={"filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}]},
        )
        search_r.raise_for_status()
        results = search_r.json().get("results", [])
        payload = {"properties": {"email": email, **properties}}
        if results:
            contact_id = results[0]["id"]
            r = await client.patch(
                f"{_BASE}/crm/v3/objects/contacts/{contact_id}",
                headers=_headers(creds),
                json=payload,
            )
        else:
            r = await client.post(
                f"{_BASE}/crm/v3/objects/contacts",
                headers=_headers(creds),
                json=payload,
            )
        r.raise_for_status()
        return r.json()


async def log_note(
    creds: Dict[str, str], contact_id: str, note: str
) -> Dict[str, Any]:
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            f"{_BASE}/crm/v3/objects/notes",
            headers=_headers(creds),
            json={"properties": {"hs_note_body": note, "hs_timestamp": "now"}},
        )
        r.raise_for_status()
        note_obj = r.json()
        # Associate note with contact
        await client.put(
            f"{_BASE}/crm/v3/objects/notes/{note_obj['id']}/associations/contacts/{contact_id}/note_to_contact",
            headers=_headers(creds),
        )
        return note_obj
