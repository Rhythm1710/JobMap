import pytest
from cryptography.fernet import Fernet


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch):
    """Keep tests from reading a developer .env or a real database."""
    monkeypatch.setenv("DATABASE_URL", "")
    monkeypatch.setenv("SERVICE_SECRET", "test-secret")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "google-client")
    monkeypatch.setenv("GOOGLE_CLIENT_SECRET", "google-secret")
    monkeypatch.setenv("GOOGLE_REDIRECT_URI", "http://localhost:3000/api/gmail/callback")
    monkeypatch.setenv("APP_URL", "http://localhost:3000")
    monkeypatch.setenv("TOKEN_ENCRYPTION_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("LLM_API_KEY", "")
    monkeypatch.setenv("SYNC_INTERVAL_MINUTES", "0")
    from app.config import get_settings
    from app.db import reset_engine

    get_settings.cache_clear()
    reset_engine()
    yield
    get_settings.cache_clear()
    reset_engine()


@pytest.fixture()
def db():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from app.db import Base
    from app import models  # noqa: F401  (register tables)

    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()
