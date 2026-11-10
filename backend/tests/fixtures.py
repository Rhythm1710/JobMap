import base64
from datetime import datetime, timedelta

from app.gmail.parse import ParsedEmail
from app.jobs.upsert import Extraction, Incoming


def parsed(
    subject: str,
    body: str,
    sender: str = "Acme <jobs@acme.com>",
    message_id: str = "m1",
    thread_id: str = "t1",
    received_at: datetime | None = None,
) -> ParsedEmail:
    return ParsedEmail(
        message_id=message_id,
        thread_id=thread_id,
        subject=subject,
        sender=sender,
        received_at=received_at or datetime(2026, 1, 15, 12, 0, 0),
        body=body,
        snippet=body[:120],
    )


def incoming(email: ParsedEmail, extraction: Extraction) -> Incoming:
    return Incoming(
        message_id=email.message_id,
        thread_id=email.thread_id,
        received_at=email.received_at,
        subject=email.subject,
        sender=email.sender,
        extraction=extraction,
    )


def gmail_payload(
    message_id: str,
    thread_id: str,
    subject: str,
    body: str,
    sender: str,
    received_at: datetime,
    html: bool = False,
) -> dict:
    encoded = base64.urlsafe_b64encode(body.encode()).decode().rstrip("=")
    mime = "text/html" if html else "text/plain"
    return {
        "id": message_id,
        "threadId": thread_id,
        "internalDate": str(int(received_at.timestamp() * 1000)),
        "snippet": "snippet",
        "payload": {
            "mimeType": mime,
            "headers": [
                {"name": "Subject", "value": subject},
                {"name": "From", "value": sender},
            ],
            "body": {"data": encoded},
        },
    }


def days_apart(start: datetime, index: int) -> datetime:
    return start + timedelta(days=index)
