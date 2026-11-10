from fastapi.testclient import TestClient

from app.config import get_settings
from app.crypto import decrypt_secret, encrypt_secret
from app.db import normalize_database_url
from app.main import app
from app.security import sign_state, verify_state


def test_health():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["ok"] is True


def test_sync_requires_the_service_secret():
    client = TestClient(app)
    denied = client.post("/gmail/sync", json={"clerkId": "user_1"})
    assert denied.status_code == 401
    wrong = client.post(
        "/gmail/sync",
        json={"clerkId": "user_1"},
        headers={"Authorization": "Bearer nope"},
    )
    assert wrong.status_code == 401


def test_oauth_start_returns_a_web_authorization_url():
    client = TestClient(app)
    response = client.post(
        "/gmail/oauth/start",
        json={"clerkId": "user_123"},
        headers={"Authorization": "Bearer test-secret"},
    )
    assert response.status_code == 200
    url = response.json()["url"]
    assert url.startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert "access_type=offline" in url
    assert "prompt=consent" in url
    assert "gmail.readonly" in url
    assert "response_type=code" in url
    assert "installed" not in url.lower()


def test_oauth_state_roundtrip_and_tamper():
    state = sign_state("user_abc", "test-secret", ttl_seconds=60)
    assert verify_state(state, "test-secret") == "user_abc"
    try:
        verify_state(state + "x", "test-secret")
        raise AssertionError("tampered state was accepted")
    except ValueError:
        pass
    try:
        verify_state(state, "other-secret")
        raise AssertionError("state from another secret was accepted")
    except ValueError:
        pass


def test_token_encryption_roundtrip():
    key = get_settings().token_encryption_key
    stored = encrypt_secret("refresh-token", key)
    assert stored != "refresh-token"
    assert decrypt_secret(stored, key) == "refresh-token"


def test_database_url_strips_prisma_pooler_params():
    url = normalize_database_url(
        "postgres://user:pass@host:5432/jobmap?schema=public&pgbouncer=true&sslmode=require"
    )
    assert url.startswith("postgresql://")
    assert "pgbouncer" not in url
    assert "schema=" not in url
    assert "sslmode=require" in url
