"""
agent/integrations/gmail.py — Gmail IMAP (read) and SMTP (send) integration.
Credentials: {"email": "...", "app_password": "..."}
"""

from __future__ import annotations

import email as email_lib
import imaplib
import smtplib
from email.mime.text import MIMEText
from typing import Any, Dict, List


def _imap_connect(creds: Dict[str, str]) -> imaplib.IMAP4_SSL:
    imap = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    imap.login(creds["email"], creds["app_password"])
    return imap


async def test_connection(creds: Dict[str, str]) -> str:
    try:
        imap = _imap_connect(creds)
        imap.logout()
        return "Gmail IMAP connection successful."
    except Exception as exc:
        raise RuntimeError(f"Gmail connection failed: {exc}") from exc


def read_unread_emails(creds: Dict[str, str], max_count: int = 10) -> List[Dict[str, Any]]:
    imap = _imap_connect(creds)
    imap.select("INBOX")
    _, data = imap.search(None, "UNSEEN")
    ids = data[0].split()[-max_count:] if data[0] else []
    results: List[Dict[str, Any]] = []
    for uid in ids:
        _, msg_data = imap.fetch(uid, "(RFC822)")
        raw = msg_data[0][1]
        msg = email_lib.message_from_bytes(raw)
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode("utf-8", errors="replace")
                    break
        else:
            body = msg.get_payload(decode=True).decode("utf-8", errors="replace")
        results.append({
            "uid": uid.decode(),
            "from": msg["From"],
            "subject": msg["Subject"],
            "snippet": body[:200],
            "body": body,
        })
        # Mark as read
        imap.store(uid, "+FLAGS", "\\Seen")
    imap.logout()
    return results


def send_email_smtp(
    creds: Dict[str, str], to: str, subject: str, body: str
) -> None:
    msg = MIMEText(body, "plain")
    msg["From"] = creds["email"]
    msg["To"] = to
    msg["Subject"] = subject
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(creds["email"], creds["app_password"])
        smtp.sendmail(creds["email"], [to], msg.as_string())
