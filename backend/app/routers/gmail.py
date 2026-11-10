import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse
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
from app.security import require_service, verify_state

logger = logging.getLogger(__name__)

router = APIRouter()


class ClerkBody(BaseModel):
    clerkId: str = Field(min_length=1, max_length=200)


def _session_or_503():
    session = create_session()
    if session is None:
        raise HTTPException(status_code=503, detail="DATABASE_URL is not configured")
    return session


@router.post("/gmail/oauth/start")
def start_oauth(body: ClerkBody, _: None = Depends(require_service)):
    settings = get_settings()
    try:
        url = build_authorization_url(body.clerkId, settings)
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"url": url}


@router.get("/gmail/oauth/callback")
def oauth_callback(code: str | None = None, state: str | None = None, error: str | None = None):
    settings = get_settings()
    destination = settings.app_url.rstrip("/") + "/jobs"
    if error or not code or not state:
        return RedirectResponse(f"{destination}?gmail=denied")
    session = create_session()
    if session is None:
        return RedirectResponse(f"{destination}?gmail=error")
    try:
        clerk_id = verify_state(state, settings.service_secret)
        tokens = exchange_code(code, settings)
        email = _profile_email(tokens, settings)
        save_connection(session, clerk_id, tokens, settings, email)
    except Exception:
        logger.exception("gmail oauth callback failed")
        session.rollback()
        return RedirectResponse(f"{destination}?gmail=error")
    finally:
        session.close()
    return RedirectResponse(f"{destination}?gmail=connected")


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
