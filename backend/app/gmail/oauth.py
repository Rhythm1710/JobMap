"""Web OAuth (authorization code), not the desktop InstalledAppFlow."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode
from uuid import uuid4

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.crypto import decrypt_secret, encrypt_secret
from app.gmail.client import GmailApiClient
from app.models import GmailConnection, utcnow
from app.security import sign_state

_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
_TOKEN_URL = "https://oauth2.googleapis.com/token"


def build_authorization_url(clerk_id: str, settings: Settings, browser_nonce: str) -> str:
    if not settings.google_configured:
        raise RuntimeError("Google OAuth client is not configured")
    if not settings.service_secret:
        raise RuntimeError("SERVICE_SECRET is not configured")
    state = sign_state(clerk_id, settings.service_secret, browser_nonce)
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": settings.gmail_scope,
        "access_type": "offline",
        "prompt": "consent",
        "include_granted_scopes": "true",
        "state": state,
    }
    return f"{_AUTH_URL}?{urlencode(params)}"


def exchange_code(code: str, settings: Settings) -> dict:
    response = httpx.post(
        _TOKEN_URL,
        data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=20,
    )
    if response.status_code >= 400:
        raise RuntimeError("Google token exchange failed")
    payload = response.json()
    if "access_token" not in payload:
        raise RuntimeError("Google token exchange returned no access token")
    return payload


def save_connection(session: Session, clerk_id: str, tokens: dict, settings: Settings, email: str | None) -> None:
    access = tokens["access_token"]
    refresh = tokens.get("refresh_token")
    expires_in = int(tokens.get("expires_in") or 3600)
    expiry = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=expires_in)
    scopes = tokens.get("scope") or settings.gmail_scope
    existing = session.scalar(select(GmailConnection).where(GmailConnection.clerkId == clerk_id))
    if refresh:
        refresh_enc = encrypt_secret(refresh, settings.token_encryption_key)
    elif existing is not None:
        refresh_enc = existing.refreshTokenEnc
    else:
        raise RuntimeError("Google did not return a refresh token. Reconnect and grant consent.")
    access_enc = encrypt_secret(access, settings.token_encryption_key)
    now = utcnow()
    if existing is None:
        session.add(
            GmailConnection(
                id=str(uuid4()),
                clerkId=clerk_id,
                email=email,
                accessTokenEnc=access_enc,
                refreshTokenEnc=refresh_enc,
                tokenExpiry=expiry,
                scopes=scopes,
                historyId=None,
                backfillBefore=None,
                backfillComplete=False,
                lastSyncedAt=None,
                lastSyncStatus=None,
                lastSyncError=None,
                createdAt=now,
                updatedAt=now,
            )
        )
    else:
        existing.email = email or existing.email
        existing.accessTokenEnc = access_enc
        existing.refreshTokenEnc = refresh_enc
        existing.tokenExpiry = expiry
        existing.scopes = scopes
        # A fresh consent should re-scan so newly granted mail is imported.
        existing.historyId = None
        existing.backfillBefore = None
        existing.backfillComplete = False
        existing.updatedAt = now
    session.commit()


def credentials_from_connection(connection: GmailConnection, settings: Settings):
    """Build google-auth Credentials and refresh the access token when it is due."""
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    access = decrypt_secret(connection.accessTokenEnc, settings.token_encryption_key)
    refresh = decrypt_secret(connection.refreshTokenEnc, settings.token_encryption_key)
    creds = Credentials(
        token=access,
        refresh_token=refresh,
        token_uri=_TOKEN_URL,
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=(connection.scopes or settings.gmail_scope).split(),
        expiry=connection.tokenExpiry,
    )
    if not creds.valid:
        if not creds.refresh_token:
            raise RuntimeError("Gmail refresh token is missing. Reconnect Gmail.")
        creds.refresh(Request())
    return creds


def persist_refreshed_credentials(session: Session, connection: GmailConnection, creds, settings: Settings) -> None:
    if not creds.token:
        return
    connection.accessTokenEnc = encrypt_secret(creds.token, settings.token_encryption_key)
    if creds.expiry:
        connection.tokenExpiry = creds.expiry
    connection.updatedAt = utcnow()
    session.add(connection)


def build_api_client(creds) -> GmailApiClient:
    from googleapiclient.discovery import build

    service = build("gmail", "v1", credentials=creds, cache_discovery=False)
    return GmailApiClient(service=service)
