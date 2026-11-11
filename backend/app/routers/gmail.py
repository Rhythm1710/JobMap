import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.config import get_settings
from app.db import create_session
from app.gmail.oauth import build_authorization_url, exchange_code, save_connection
from app.gmail.sync import (
    GmailNotConnected,
    execute_sync,
    mark_sync_error,
    safe_error_text,
    sync_all,
)
from app.models import GmailConnection, utcnow
from app.security import OauthBindingError, require_browser_binding, require_service

logger = logging.getLogger(__name__)

router = APIRouter()


class ClerkBody(BaseModel):
    clerkId: str = Field(min_length=1, max_length=200)


class StartOAuthBody(BaseModel):
    clerkId: str = Field(min_length=1, max_length=200)
    browserNonce: str = Field(min_length=16, max_length=200)


class CompleteOAuthBody(BaseModel):
    code: str = Field(min_length=1, max_length=2048)
    state: str = Field(min_length=1, max_length=4096)
    browserNonce: str | None = None


def _session_or_503():
    session = create_session()
    if session is None:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    return session


@router.post("/gmail/oauth/start")
def start_oauth(body: StartOAuthBody, _: None = Depends(require_service)):
    settings = get_settings()
    try:
        url = build_authorization_url(body.clerkId, settings, body.browserNonce)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"url": url}


@router.post("/gmail/oauth/complete")
def complete_oauth(body: CompleteOAuthBody, _: None = Depends(require_service)):
    """Exchange the Google code only when the browser nonce matches the signed state.

    The Next.js callback sends the httpOnly cookie value as browserNonce. A missing
    or mismatched value is the case where someone approved a consent URL that a
    different browser started. Do not call Google before that check.
    """
    settings = get_settings()
    try:
        clerk_id = require_browser_binding(body.state, settings.service_secret, body.browserNonce)
    except OauthBindingError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    session = _session_or_503()
    try:
        tokens = exchange_code(body.code, settings)
        email = _profile_email(tokens, settings)
        save_connection(session, clerk_id, tokens, settings, email)
    except Exception:
        logger.exception("gmail oauth complete failed")
        session.rollback()
        raise HTTPException(status_code=502, detail="Gmail connect failed")
    finally:
        session.close()
    return {"ok": True, "email": email}


def _profile_email(tokens: dict, settings) -> str | None:
    try:
        from google.oauth2.credentials import Credentials

        from app.gmail.oauth import build_api_client

        creds = Credentials(token=tokens.get("access_token"), scopes=settings.gmail_scope.split())
        profile = build_api_client(creds).get_profile()
        return profile.get("emailAddress")
    except Exception:
        logger.warning("gmail profile lookup failed after oauth")
        return None


@router.post("/gmail/sync")
def sync_one(body: ClerkBody, _: None = Depends(require_service)):
    settings = get_settings()
    session = _session_or_503()
    try:
        stats = execute_sync(session, body.clerkId, settings)
        connection = session.scalar(select(GmailConnection).where(GmailConnection.clerkId == body.clerkId))
        return {
            "ok": True,
            **stats.as_dict(),
            "lastSyncedAt": connection.lastSyncedAt.isoformat() if connection and connection.lastSyncedAt else None,
            "backfillComplete": bool(connection.backfillComplete) if connection else False,
        }
    except GmailNotConnected:
        raise HTTPException(status_code=409, detail="Gmail is not connected")
    except Exception as error:
        logger.exception("gmail sync failed")
        session.rollback()
        mark_sync_error(session, body.clerkId, safe_error_text(error))
        raise HTTPException(status_code=502, detail="Gmail sync failed")
    finally:
        session.close()


@router.post("/gmail/disconnect")
def disconnect(body: ClerkBody, _: None = Depends(require_service)):
    session = _session_or_503()
    try:
        connection = session.scalar(select(GmailConnection).where(GmailConnection.clerkId == body.clerkId))
        if connection is not None:
            session.delete(connection)
            session.commit()
        return {"ok": True}
    finally:
        session.close()


@router.post("/internal/cron/sync")
def cron_sync(_: None = Depends(require_service)):
    settings = get_settings()
    try:
        results = sync_all(settings)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"ok": True, "results": results, "ranAt": utcnow().isoformat()}
