from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from app.db import Base
from app.main import app
from app.models import GmailConnection
from app.security import (
    MISMATCH_OAUTH_COOKIE,
    MISSING_OAUTH_COOKIE,
    require_browser_binding,
    sign_state,
)


NONCE = "browser-nonce-value-0123456789abcdef"
OTHER = "other-browser-nonce-0123456789abcd"
AUTH = {"Authorization": "Bearer test-secret"}


def _client() -> TestClient:
    return TestClient(app)


def _state(nonce: str = NONCE, clerk_id: str = "user_1") -> str:
    return sign_state(clerk_id, "test-secret", nonce)


def test_binding_accepts_the_nonce_that_started_the_flow():
    clerk_id = require_browser_binding(_state(), "test-secret", NONCE)
    assert clerk_id == "user_1"


def test_binding_rejects_a_missing_cookie():
    for missing in (None, "", "   "):
        try:
            require_browser_binding(_state(), "test-secret", missing)
            raise AssertionError("missing cookie was accepted")
        except Exception as error:
            assert error.reason == "missing"
            assert str(error) == MISSING_OAUTH_COOKIE


def test_binding_rejects_a_mismatched_cookie():
    try:
        require_browser_binding(_state(), "test-secret", OTHER)
        raise AssertionError("mismatched cookie was accepted")
    except Exception as error:
        assert error.reason == "mismatch"
        assert str(error) == MISMATCH_OAUTH_COOKIE


def test_complete_stores_the_connection_when_the_cookie_matches(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    monkeypatch.setattr("app.routers.gmail.create_session", Session)
    monkeypatch.setattr(
        "app.routers.gmail.exchange_code",
        lambda code, settings: {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
        },
    )
    monkeypatch.setattr("app.routers.gmail._profile_email", lambda tokens, settings: "ada@example.com")

    response = _client().post(
        "/gmail/oauth/complete",
        json={"code": "google-code", "state": _state(), "browserNonce": NONCE},
        headers=AUTH,
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["email"] == "ada@example.com"

    session = Session()
    try:
        row = session.scalar(select(GmailConnection).where(GmailConnection.clerkId == "user_1"))
        assert row is not None
        assert row.email == "ada@example.com"
        assert row.refreshTokenEnc != "refresh-token"
    finally:
        session.close()


def test_complete_does_not_exchange_when_the_cookie_is_missing_or_wrong(monkeypatch):
    calls = []
    monkeypatch.setattr(
        "app.routers.gmail.exchange_code",
        lambda code, settings: calls.append(code) or {},
    )
    client = _client()
    state = _state()

    missing = client.post(
        "/gmail/oauth/complete",
        json={"code": "google-code", "state": state},
        headers=AUTH,
    )
    assert missing.status_code == 403
    assert missing.json()["detail"] == MISSING_OAUTH_COOKIE

    mismatch = client.post(
        "/gmail/oauth/complete",
        json={"code": "google-code", "state": state, "browserNonce": OTHER},
        headers=AUTH,
    )
    assert mismatch.status_code == 403
    assert mismatch.json()["detail"] == MISMATCH_OAUTH_COOKIE
    assert calls == []
