"""
agent/integrations/google_calendar.py — Google Calendar API helpers.
Credentials: {"client_id", "client_secret", "refresh_token"}
User obtains refresh_token via Google OAuth Playground with Calendar scope.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def _get_service(creds_dict: Dict[str, str]):
    from google.auth.transport.requests import Request
    creds = Credentials(
        token=None,
        refresh_token=creds_dict.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_dict.get("client_id"),
        client_secret=creds_dict.get("client_secret"),
        scopes=["https://www.googleapis.com/auth/calendar.events", "https://www.googleapis.com/auth/calendar.readonly"],
    )
    creds.refresh(Request())
    return build("calendar", "v3", credentials=creds)


async def test_connection(creds: Dict[str, str]) -> str:
    try:
        service = _get_service(creds)
        service.events().list(calendarId="primary", maxResults=1).execute()
        return "Google Calendar connected."
    except Exception as exc:
        raise RuntimeError(f"Calendar connection failed: {exc}") from exc


def list_upcoming_events(creds: Dict[str, str], max_results: int = 10, days_ahead: int = 7) -> List[Dict[str, Any]]:
    service = _get_service(creds)
    now = datetime.now(timezone.utc)
    time_min = now.isoformat()
    time_max = (now + timedelta(days=days_ahead)).isoformat()
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    events = events_result.get("items", [])
    out: List[Dict[str, Any]] = []
    for e in events:
        start = e.get("start", {})
        start_str = start.get("dateTime", start.get("date", "?"))
        out.append({
            "id": e.get("id"),
            "summary": e.get("summary", "(No title)"),
            "start": start_str,
            "organizer": e.get("organizer", {}).get("email", ""),
        })
    return out


def create_event(
    creds: Dict[str, str],
    summary: str,
    start_datetime: str,
    end_datetime: str | None = None,
    description: str = "",
) -> Dict[str, Any]:
    from datetime import datetime, timedelta
    service = _get_service(creds)
    end = (end_datetime or "").strip() or None
    if not end:
        try:
            start_dt = datetime.fromisoformat(start_datetime.replace("Z", "+00:00"))
            end_dt = start_dt + timedelta(hours=1)
            end = end_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00")
        except Exception:
            end = start_datetime
    body = {
        "summary": summary,
        "description": description,
        "start": {"dateTime": start_datetime, "timeZone": "UTC"},
        "end": {"dateTime": end, "timeZone": "UTC"},
    }
    event = service.events().insert(calendarId="primary", body=body).execute()
    return {"id": event.get("id"), "htmlLink": event.get("htmlLink")}
