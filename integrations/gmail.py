"""
Gmail integration: read via IMAP, send via SMTP.
Uses stored credentials (email + app password). Never logs credentials.
"""

from __future__ import annotations

import imaplib
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Any, Dict, List, Optional

# Default Gmail IMAP/SMTP
IMAP_HOST = "imap.gmail.com"
IMAP_PORT = 993
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587


def test_connection(creds: Dict[str, Any]) -> tuple[bool, str]:
    """
    Test IMAP login. creds must have 'email' and 'app_password'.
    Returns (success, message).
    """
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(creds["email"], creds["app_password"])
        mail.logout()
        return True, "Connected successfully"
    except Exception as e:
        return False, str(e) if "Authentication failed" in str(e) or "credentials" in str(e).lower() else "Connection failed"


def read_unread_emails(creds: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
    """
    Read unread emails from inbox. Marks as read after fetching.
    Returns list of dicts: sender, subject, snippet, body, message_id.
    """
    results: List[Dict[str, Any]] = []
    try:
        mail = imaplib.IMAP4_SSL(IMAP_HOST, IMAP_PORT)
        mail.login(creds["email"], creds["app_password"])
        mail.select("INBOX")
        status, data = mail.search(None, "UNSEEN")
        if status != "OK" or not data[0]:
            mail.logout()
            return results
        ids = data[0].split()
        for mid in ids[-limit:][::-1]:
            status, msg_data = mail.fetch(mid, "(RFC822)")
            if status != "OK" or not msg_data:
                continue
            raw = msg_data[0][1]
            if isinstance(raw, bytes):
                from email import message_from_bytes
                msg = message_from_bytes(raw)
            else:
                from email import message_from_string
                msg = message_from_string(raw)
            sender = msg.get("From", "")
            subject = msg.get("Subject", "")
            body = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        body = part.get_payload(decode=True)
                        if body:
                            body = body.decode("utf-8", errors="replace")
                        break
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode("utf-8", errors="replace")
            snippet = (body or "")[:200].replace("\n", " ")
            results.append({
                "message_id": mid.decode() if isinstance(mid, bytes) else str(mid),
                "sender": sender,
                "subject": subject,
                "snippet": snippet,
                "body": body,
            })
            mail.store(mid, "+FLAGS", "\\Seen")
        mail.logout()
    except Exception:
        raise
    return results


def send_email(creds: Dict[str, Any], to: str, subject: str, body: str, reply_to_id: Optional[str] = None) -> tuple[bool, str]:
    """
    Send email via SMTP. Returns (success, message).
    """
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = creds["email"]
        msg["To"] = to
        msg.attach(MIMEText(body, "plain"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(creds["email"], creds["app_password"])
            server.sendmail(creds["email"], to, msg.as_string())
        return True, "Email sent"
    except Exception as e:
        return False, str(e)
