import json
from datetime import datetime

import httpx

from app.classify.llm import LLMClassifier, parse_llm_payload, prepare_email_text
from app.classify.pipeline import classify_email
from app.config import Settings
from app.gmail.parse import ParsedEmail


def _settings(**overrides) -> Settings:
    values = {
        "llm_api_key": "test-key",
        "llm_base_url": "https://api.groq.com/openai/v1",
        "llm_model": "llama-3.3-70b-versatile",
        "llm_max_body_chars": 80,
        "llm_max_calls_per_run": 2,
        "llm_max_retries": 2,
        "llm_retry_base_seconds": 0,
    }
    values.update(overrides)
    return Settings(**values)


def _email() -> ParsedEmail:
    quoted = "\n".join(
        [
            "We are hiring and would like to talk.",
            "> older quoted reply that should not be sent",
            "Unsubscribe from these emails",
            "padding " * 40,
        ]
    )
    return ParsedEmail(
        message_id="m1",
        thread_id="t1",
        subject="A note",
        sender="Recruiter <r@example.com>",
        received_at=datetime(2026, 5, 1, 12, 0, 0),
        body=quoted,
        snippet="",
    )


def _completion(content: str, status: int = 200, headers: dict | None = None) -> httpx.Response:
    return httpx.Response(
        status,
        headers=headers or {},
        json={"choices": [{"message": {"content": content}}]},
    )


class ScriptedClient:
    def __init__(self, responses: list[httpx.Response]):
        self.responses = list(responses)
        self.requests: list[dict] = []

    def post(self, url, headers=None, json=None):
        self.requests.append({"url": url, "headers": headers, "json": json})
        return self.responses.pop(0)

    def close(self):
        return None


def test_prepare_email_text_strips_quotes_and_truncates():
    text = prepare_email_text(_email(), 80)
    assert "quoted reply" not in text
    assert "Unsubscribe" not in text
    assert text.endswith("...")
    assert "From: Recruiter" in text


def test_valid_json_is_accepted_and_junk_is_rejected():
    good = parse_llm_payload(
        {
            "is_application": True,
            "company": "Linear",
            "position": "Designer",
            "status": "interview",
            "mode": "full-time",
            "confidence": 0.8,
        }
    )
    assert good is not None
    assert good.company == "Linear"
    assert good.status == "interview"
    assert parse_llm_payload(["not", "an", "object"]) is None
    assert parse_llm_payload({"is_application": "yes", "status": "applied"}) is None
    assert parse_llm_payload({"is_application": True, "status": "hired"}) is None


def test_retries_429_then_uses_the_model_result():
    body = json.dumps(
        {
            "is_application": True,
            "company": "Plaid",
            "position": "Support Engineer",
            "status": "applied",
            "mode": None,
            "confidence": 0.66,
        }
    )
    client = ScriptedClient(
        [
            httpx.Response(429, headers={"retry-after": "0"}, json={"error": "slow down"}),
            _completion(body),
        ]
    )
    slept: list[float] = []
    result = LLMClassifier(_settings(), client, sleeper=slept.append).classify(_email())
    assert result is not None
    assert result.company == "Plaid"
    assert result.status == "applied"
    assert slept == [0.0]
    assert len(client.requests) == 2
    sent = client.requests[0]["json"]["messages"][1]["content"]
    assert "quoted reply" not in sent
    assert len(sent) < 400


def test_exhausted_rate_limit_and_junk_fall_back_to_rules():
    limited = ScriptedClient(
        [
            httpx.Response(429, headers={"retry-after": "0"}, json={}),
            httpx.Response(429, headers={"retry-after": "0"}, json={}),
            httpx.Response(429, headers={"retry-after": "0"}, json={}),
        ]
    )
    classifier = LLMClassifier(_settings(), limited, sleeper=lambda _delay: None)
    email = _email()
    assert classifier.classify(email) is None
    rules = classify_email(email, classifier)
    assert rules.reason != "llm"
    assert rules.is_application is False

    junk = ScriptedClient([_completion("sure, here is some prose instead of json")])
    again = LLMClassifier(_settings(), junk, sleeper=lambda _delay: None)
    assert again.classify(email) is None
    assert classify_email(email, again).is_application is False


def test_call_budget_skips_the_provider():
    client = ScriptedClient(
        [
            _completion(
                json.dumps(
                    {"is_application": False, "status": None, "mode": None, "confidence": 0.2}
                )
            ),
            _completion(
                json.dumps(
                    {"is_application": False, "status": None, "mode": None, "confidence": 0.2}
                )
            ),
        ]
    )
    classifier = LLMClassifier(_settings(llm_max_calls_per_run=1), client, sleeper=lambda _delay: None)
    assert classifier.classify(_email()) is not None
    assert classifier.classify(_email()) is None
    assert len(client.requests) == 1


def test_openrouter_requests_include_attribution_headers():
    client = ScriptedClient(
        [
            _completion(
                json.dumps({"is_application": False, "status": None, "mode": None, "confidence": 0.4})
            )
        ]
    )
    settings = _settings(
        llm_base_url="https://openrouter.ai/api/v1",
        llm_model="meta-llama/llama-3.3-70b-instruct:free",
        app_url="https://jobmap.example",
    )
    LLMClassifier(settings, client, sleeper=lambda _delay: None).classify(_email())
    headers = client.requests[0]["headers"]
    assert headers["HTTP-Referer"] == "https://jobmap.example"
    assert headers["X-Title"] == "JobMap"
