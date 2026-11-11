"""OpenAI-compatible chat client aimed at free-tier hosts (Groq, OpenRouter, Gemini).

Rules stay the source of truth. This client returns None when the model is
rate-limited past the retry budget, returns junk, or the per-sync call cap is hit.
The pipeline then keeps the rules result.
"""

from __future__ import annotations

import json
import logging
import re
import time

import httpx

from app.config import Settings
from app.gmail.parse import ParsedEmail
from app.jobs.upsert import Extraction

logger = logging.getLogger(__name__)

_ALLOWED_STATUS = {"applied", "assessment", "interview", "rejected", "offer"}
_ALLOWED_MODE = {"full-time", "part-time", "internship"}

_SYSTEM = (
    "You extract job-application facts from a single email. "
    "Reply with one JSON object and no markdown. Use null when unknown. "
    "Keys: is_application (boolean), company, position, status, location, mode, job_url, confidence. "
    "status must be applied, assessment, interview, rejected, offer, or null. "
    "Set is_application true only for the recipient's own application, interview, "
    "assessment, rejection, or offer. Newsletters and job alerts are false. "
    "mode is full-time, part-time, internship, or null."
)

_FOOTER = re.compile(r"unsubscribe|view in browser|view this email|sent from my|confidentiality notice", re.I)


def prepare_email_text(email: ParsedEmail, limit: int) -> str:
    """Drop quoted replies and footers, then cap the body so a free tier stays cheap."""
    lines: list[str] = []
    for raw in (email.body or "").splitlines():
        line = raw.strip()
        if not line or line.startswith(">"):
            continue
        if _FOOTER.search(line):
            continue
        lines.append(line)
    body = re.sub(r"\n{2,}", "\n", "\n".join(lines)).strip()
    if len(body) > limit:
        body = body[:limit].rstrip() + "..."
    subject = (email.subject or "").strip()[:200]
    sender = (email.sender or "").strip()[:160]
    return f"From: {sender}\nSubject: {subject}\nDate: {email.received_at.date().isoformat()}\n\n{body}"


def _as_bool(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
        return value.strip().lower() == "true"
    return None


def _text(data: dict, key: str, limit: int) -> str | None:
    value = data.get(key)
    if not isinstance(value, str):
        return None
    value = " ".join(value.split())
    if not value or value.lower() == "null" or not re.search(r"[A-Za-z]", value):
        return None
    return value[:limit]


def parse_llm_payload(data: object) -> Extraction | None:
    """Accept only a small JSON object. Anything else is junk and must be ignored."""
    if not isinstance(data, dict):
        return None
    is_application = _as_bool(data.get("is_application"))
    if is_application is None:
        return None
    raw_status = data.get("status")
    if raw_status in (None, "", "null"):
        status = None
    elif isinstance(raw_status, str) and raw_status in _ALLOWED_STATUS:
        status = raw_status
    else:
        return None
    raw_mode = data.get("mode")
    if raw_mode in (None, "", "null"):
        mode = None
    elif isinstance(raw_mode, str) and raw_mode in _ALLOWED_MODE:
        mode = raw_mode
    else:
        return None
    if status and not is_application:
        is_application = True
    try:
        confidence = float(data.get("confidence") or 0.0)
    except (TypeError, ValueError):
        confidence = 0.0
    confidence = max(0.0, min(confidence, 1.0))
    job_url = _text(data, "job_url", 500)
    if job_url and not job_url.lower().startswith(("http://", "https://")):
        job_url = None
    return Extraction(
        is_application=is_application,
        company=_text(data, "company", 80),
        position=_text(data, "position", 120),
        status=status,
        location=_text(data, "location", 80),
        mode=mode,
        job_url=job_url,
        confidence=confidence or (0.7 if is_application else 0.6),
        needs_review=False,
        reason="llm",
    )


def _json_from_content(content: str) -> dict | None:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text, flags=re.I).strip()
        text = re.sub(r"```$", "", text).strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return None
    return parsed if isinstance(parsed, dict) else None


def _retry_delay(response: httpx.Response, attempt: int, base_seconds: float) -> float:
    header = response.headers.get("retry-after")
    if header:
        try:
            return min(float(header), 30.0)
        except ValueError:
            pass
    return min(base_seconds * (2**attempt), 30.0)


class LLMClassifier:
    def __init__(self, settings: Settings, client: httpx.Client | None = None, sleeper=time.sleep):
        self.settings = settings
        self._client = client
        self._sleeper = sleeper
        self.calls = 0

    @property
    def enabled(self) -> bool:
        return self.settings.llm_enabled and self.settings.llm_max_calls_per_run > 0

    def _headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        if "openrouter.ai" in self.settings.llm_base_url:
            headers["HTTP-Referer"] = self.settings.app_url or "http://localhost:3000"
            headers["X-Title"] = "JobMap"
        return headers

    def _post(self, client: httpx.Client, url: str, payload: dict) -> httpx.Response | None:
        dropped_format = False
        attempt = 0
        while True:
            response = client.post(url, headers=self._headers(), json=payload)
            if response.status_code == 429 and attempt < self.settings.llm_max_retries:
                delay = _retry_delay(response, attempt, self.settings.llm_retry_base_seconds)
                logger.info("llm rate limited; retrying in %.1fs", delay)
                self._sleeper(delay)
                attempt += 1
                continue
            if (
                response.status_code == 400
                and not dropped_format
                and "response_format" in payload
                and "response_format" in response.text.lower()
            ):
                payload = {key: value for key, value in payload.items() if key != "response_format"}
                dropped_format = True
                continue
            if response.status_code >= 400:
                logger.warning("llm request failed with status %s", response.status_code)
                return None
            return response

    def classify(self, email: ParsedEmail) -> Extraction | None:
        if not self.enabled:
            return None
        if self.calls >= self.settings.llm_max_calls_per_run:
            logger.info("llm call budget reached (%s)", self.settings.llm_max_calls_per_run)
            return None
        self.calls += 1
        user = prepare_email_text(email, self.settings.llm_max_body_chars)
        payload = {
            "model": self.settings.llm_model,
            "temperature": 0,
            "max_tokens": 300,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": user},
            ],
        }
        url = self.settings.llm_base_url.rstrip("/") + "/chat/completions"
        owns_client = self._client is None
        client = self._client or httpx.Client(timeout=30)
        try:
            response = self._post(client, url, payload)
            if response is None:
                return None
            content = response.json()["choices"][0]["message"]["content"]
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError):
            logger.warning("llm classification failed for message %s", email.message_id)
            return None
        finally:
            if owns_client:
                client.close()
        if not isinstance(content, str):
            return None
        return parse_llm_payload(_json_from_content(content))
