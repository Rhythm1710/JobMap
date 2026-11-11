"""OpenAI-compatible chat completion client. Any provider that speaks this API works."""

from __future__ import annotations

import json
import logging
import re

import httpx

from app.config import Settings
from app.gmail.parse import ParsedEmail
from app.jobs.upsert import Extraction

logger = logging.getLogger(__name__)

_ALLOWED_STATUS = {"applied", "assessment", "interview", "rejected", "offer"}
_ALLOWED_MODE = {"full-time", "part-time", "internship"}

_SYSTEM = (
    "You extract job-application facts from a single email. "
    "Reply with JSON only, no markdown. Use null when unknown. "
    "status must be one of: applied, assessment, interview, rejected, offer, or null. "
    "Set is_application true only when the email is about the recipient's own application, "
    "interview, assessment, rejection, or offer. Newsletters and generic job alerts are false. "
    "mode is full-time, part-time, internship, or null."
)


def parse_llm_payload(data: dict) -> Extraction | None:
    if not isinstance(data, dict):
        return None
    status = data.get("status")
    if status not in _ALLOWED_STATUS:
        status = None
    mode = data.get("mode")
    if mode not in _ALLOWED_MODE:
        mode = None
    is_application = bool(data.get("is_application"))
    if status and not is_application:
        # A concrete status implies this is application mail.
        is_application = True

    def _text(key: str, limit: int) -> str | None:
        value = data.get(key)
        if not isinstance(value, str):
            return None
        value = value.strip()
        if not value or value.lower() == "null":
            return None
        return value[:limit]

    try:
        confidence = float(data.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(confidence, 1.0))
    return Extraction(
        is_application=is_application,
        company=_text("company", 80),
        position=_text("position", 120),
        status=status,
        location=_text("location", 80),
        mode=mode,
        job_url=_text("job_url", 500),
        confidence=confidence or (0.7 if is_application else 0.6),
        needs_review=False,
        reason="llm",
    )


def _json_from_content(content: str) -> dict | None:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


class LLMClassifier:
    def __init__(self, settings: Settings, client: httpx.Client | None = None):
        self.settings = settings
        self._client = client

    @property
    def enabled(self) -> bool:
        return self.settings.llm_enabled

    def classify(self, email: ParsedEmail) -> Extraction | None:
        if not self.enabled:
            return None
        body = (email.body or "")[:6000]
        user = (
            f"From: {email.sender}\n"
            f"Subject: {email.subject}\n"
            f"Date: {email.received_at.isoformat()}\n\n"
            f"{body}"
        )
        payload = {
            "model": self.settings.llm_model,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
        }
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        url = self.settings.llm_base_url.rstrip("/") + "/chat/completions"
        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=30)
        try:
            response = client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, ValueError):
            logger.warning("llm classification failed for message %s", email.message_id)
            return None
        finally:
            if owns_client:
                client.close()
        parsed = _json_from_content(content) if isinstance(content, str) else None
        if parsed is None:
            return None
        return parse_llm_payload(parsed)
