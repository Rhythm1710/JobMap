"""Turn a Gmail API message resource into plain text fields."""

from __future__ import annotations

import base64
import re
from dataclasses import dataclass
from datetime import datetime, timezone

from bs4 import BeautifulSoup


@dataclass
class ParsedEmail:
    message_id: str
    thread_id: str
    subject: str
    sender: str
    received_at: datetime
    body: str
    snippet: str


def _decode_b64(data: str) -> str:
    padded = data + "=" * (-len(data) % 4)
    raw = base64.urlsafe_b64decode(padded.encode())
    return raw.decode("utf-8", errors="replace")


def _walk(payload: dict) -> tuple[list[str], list[str]]:
    mime = payload.get("mimeType", "")
    data = (payload.get("body") or {}).get("data")
    texts: list[str] = []
    htmls: list[str] = []
    if data and mime == "text/plain":
        texts.append(_decode_b64(data))
    elif data and mime == "text/html":
        htmls.append(_decode_b64(data))
    for part in payload.get("parts") or []:
        child_text, child_html = _walk(part)
        texts.extend(child_text)
        htmls.extend(child_html)
    return texts, htmls


def _html_to_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    return soup.get_text("\n")


def _collapse(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_gmail_message(message: dict) -> ParsedEmail:
    payload = message.get("payload") or {}
    headers = {
        (header.get("name") or "").lower(): header.get("value") or ""
        for header in payload.get("headers") or []
    }
    texts, htmls = _walk(payload)
    if texts:
        body = "\n".join(texts)
    elif htmls:
        body = _html_to_text("\n".join(htmls))
    else:
        body = ""
    body = _collapse(body)[:20000]
    snippet = _collapse(message.get("snippet") or "")
    if not body:
        body = snippet
    millis = int(message.get("internalDate") or "0")
    if millis:
        received_at = datetime.fromtimestamp(millis / 1000, timezone.utc).replace(tzinfo=None)
    else:
        received_at = datetime.now(timezone.utc).replace(tzinfo=None)
    return ParsedEmail(
        message_id=message.get("id") or "",
        thread_id=message.get("threadId") or "",
        subject=headers.get("subject", ""),
        sender=headers.get("from", ""),
        received_at=received_at,
        body=body,
        snippet=snippet,
    )
