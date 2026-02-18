"""
HubSpot CRM integration via Private App token.
Create/update contacts and log activity notes. Never logs tokens.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

import requests

BASE = "https://api.hubapi.com"


def test_connection(creds: Dict[str, Any]) -> tuple[bool, str]:
    """Test token with a minimal API call. creds: access_token."""
    try:
        r = requests.get(
            f"{BASE}/crm/v3/objects/contacts",
            headers={"Authorization": f"Bearer {creds['access_token']}"},
            params={"limit": 1},
            timeout=10,
        )
        if r.status_code in (200, 204):
            return True, "Connected successfully"
        return False, r.text or f"HTTP {r.status_code}"
    except Exception as e:
        return False, str(e)


def create_or_update_contact(creds: Dict[str, Any], email: str, properties: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Search by email, create if not found, update if found. Returns contact id.
    """
    token = creds["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    # Search by email
    r = requests.post(
        f"{BASE}/crm/v3/objects/contacts/search",
        headers=headers,
        json={"filterGroups": [{"filters": [{"propertyName": "email", "operator": "EQ", "value": email}]}], "limit": 1},
        timeout=10,
    )
    if r.status_code == 200 and r.json().get("results"):
        contact_id = r.json()["results"][0]["id"]
        if properties:
            requests.patch(
                f"{BASE}/crm/v3/objects/contacts/{contact_id}",
                headers=headers,
                json={"properties": properties},
                timeout=10,
            )
        return contact_id
    # Create
    props = {"email": email, **(properties or {})}
    r = requests.post(
        f"{BASE}/crm/v3/objects/contacts",
        headers=headers,
        json={"properties": {k: str(v) for k, v in props.items()}},
        timeout=10,
    )
    if r.status_code in (200, 201):
        return r.json().get("id")
    return None


def log_activity_note(creds: Dict[str, Any], contact_id: str, body: str) -> Optional[str]:
    """Create an engagement note for a contact. Returns note id."""
    token = creds["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    r = requests.post(
        f"{BASE}/crm/v3/objects/notes",
        headers=headers,
        json={
            "properties": {"hs_note_body": body},
            "associations": [{"to": {"id": contact_id}, "types": [{"associationCategory": "HUBSPOT_DEFINED", "associationTypeId": 202}]}],
        },
        timeout=10,
    )
    if r.status_code in (200, 201):
        return r.json().get("id")
    return None
