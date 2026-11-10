"""Idempotent Gmail import. Re-running a sync does not duplicate applications."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.classify.llm import LLMClassifier
from app.classify.pipeline import classify_email
from app.config import Settings
from app.gmail.client import GmailApiClient, HistoryExpired, MessageGone
from app.gmail.parse import parse_gmail_message
from app.gmail.search import build_search_query
from app.jobs.repository import (
    apply_decision,
    backfill_keys,
    load_user_state,
    record_message_gone,
)
from app.jobs.upsert import Incoming, fold_state, plan_decision
from app.models import GmailConnection, utcnow

logger = logging.getLogger(__name__)


class GmailNotConnected(Exception):
    pass


@dataclass
class SyncStats:
    created: int = 0
    updated: int = 0
    ignored: int = 0
    deferred: int = 0
    skipped: int = 0
    errors: int = 0

    def add(self, disposition: str) -> None:
        if disposition == "created":
            self.created += 1
        elif disposition == "linked":
            self.updated += 1
        elif disposition == "ignored":
            self.ignored += 1
        elif disposition == "deferred":
            self.deferred += 1
        elif disposition == "skipped":
            self.skipped += 1

    def as_dict(self) -> dict:
        return {
            "created": self.created,
            "updated": self.updated,
            "ignored": self.ignored,
            "deferred": self.deferred,
            "skipped": self.skipped,
            "errors": self.errors,
        }


@dataclass
class _Batch:
    ids: list[str] = field(default_factory=list)
    history_cursor: str | None = None
    backfill_ids: list[str] = field(default_factory=list)
    backfill_exhausted: bool = False
    backfill_attempted: bool = False


def _collect_ids(client: GmailApiClient, connection: GmailConnection, settings: Settings, deferred: set[str]) -> _Batch:
    batch = _Batch()
    limit = max(settings.gmail_max_messages_per_run, 1)
    profile = client.get_profile()
    profile_history = str(profile.get("historyId") or "")

    if connection.historyId:
        try:
            history = client.list_history(connection.historyId, limit)
            batch.ids.extend(history.message_ids)
            batch.history_cursor = history.latest_history_id or profile_history
        except HistoryExpired:
            logger.info("gmail history expired for %s; restarting backfill", connection.clerkId)
            connection.historyId = None
            connection.backfillComplete = False
            connection.backfillBefore = None
            batch.history_cursor = profile_history
    else:
        batch.history_cursor = profile_history

    remaining = max(limit - len(batch.ids), 0)
    if not connection.backfillComplete and remaining:
        query = build_search_query(settings.gmail_lookback_days, connection.backfillBefore)
        page = client.list_messages(query, remaining)
        batch.backfill_attempted = True
        batch.backfill_ids = page.ids
        batch.backfill_exhausted = page.exhausted
        batch.ids.extend(page.ids)

    for message_id in list(deferred)[:50]:
        batch.ids.append(message_id)
    batch.ids = list(dict.fromkeys(batch.ids))
    return batch


def sync_connection(
    session: Session,
    connection: GmailConnection,
    client: GmailApiClient,
    settings: Settings,
    llm: LLMClassifier | None = None,
) -> SyncStats:
    stats = SyncStats()
    backfill_keys(session)
    state = load_user_state(session, connection.clerkId)
    batch = _collect_ids(client, connection, settings, state.deferred_message_ids)

    parsed = []
    backfill_times = []
    for message_id in batch.ids:
        if message_id in state.seen_message_ids:
            stats.skipped += 1
            continue
        try:
            raw = client.get_message(message_id)
            email = parse_gmail_message(raw)
        except MessageGone:
            record_message_gone(session, connection.clerkId, message_id)
            state.seen_message_ids.add(message_id)
            state.deferred_message_ids.discard(message_id)
            stats.ignored += 1
            continue
        except Exception:
            logger.exception("failed to fetch gmail message %s", message_id)
            stats.errors += 1
            continue
        parsed.append(email)
        if message_id in batch.backfill_ids:
            backfill_times.append(email.received_at)

    parsed.sort(key=lambda email: email.received_at)
    for email in parsed:
        try:
            extraction = classify_email(email, llm)
            incoming = Incoming(
                message_id=email.message_id,
                thread_id=email.thread_id,
                received_at=email.received_at,
                subject=email.subject,
                sender=email.sender,
                extraction=extraction,
            )
            decision = plan_decision(state, incoming, connection.clerkId)
            disposition = apply_decision(session, connection.clerkId, decision, incoming)
            fold_state(state, decision, incoming)
            stats.add(disposition)
        except Exception:
            logger.exception("failed to classify message %s", email.message_id)
            stats.errors += 1

    # A failed message is not recorded, so the cursors stay put and the next run retries it.
    # Messages that did import are skipped on that retry.
    if stats.errors == 0:
        if batch.history_cursor:
            connection.historyId = batch.history_cursor
        if batch.backfill_attempted:
            if batch.backfill_exhausted or not batch.backfill_ids or not backfill_times:
                # An empty page, or a page we have already imported, ends the backfill.
                # New mail still arrives through the history cursor.
                connection.backfillComplete = True
            else:
                oldest = min(backfill_times)
                new_before = oldest - timedelta(seconds=1)
                if connection.backfillBefore and new_before >= connection.backfillBefore:
                    connection.backfillComplete = True
                else:
                    connection.backfillBefore = new_before
    profile = {}
    try:
        profile = client.get_profile()
    except Exception:
        profile = {}
    if profile.get("emailAddress") and not connection.email:
        connection.email = profile["emailAddress"]
    connection.lastSyncedAt = utcnow()
    connection.lastSyncStatus = "ok" if stats.errors == 0 else "partial"
    connection.lastSyncError = None if stats.errors == 0 else f"{stats.errors} message(s) failed"
    connection.updatedAt = utcnow()
    session.commit()
    logger.info(
        "synced gmail for %s created=%s updated=%s skipped=%s",
        connection.clerkId,
        stats.created,
        stats.updated,
        stats.skipped,
    )
    return stats


def sync_clerk(session: Session, clerk_id: str, client: GmailApiClient, settings: Settings, llm: LLMClassifier | None = None) -> SyncStats:
    connection = session.scalar(select(GmailConnection).where(GmailConnection.clerkId == clerk_id))
    if connection is None:
        raise GmailNotConnected(clerk_id)
    return sync_connection(session, connection, client, settings, llm)


def safe_error_text(error: Exception) -> str:
    import re

    text = str(error) or error.__class__.__name__
    text = re.sub(r"ya29\.[0-9A-Za-z\-_]+", "[token]", text)
    text = re.sub(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]+=*", "bearer [secret]", text)
    return text[:300]


def mark_sync_error(session: Session, clerk_id: str, message: str) -> None:
    connection = session.scalar(select(GmailConnection).where(GmailConnection.clerkId == clerk_id))
    if connection is None:
        return
    connection.lastSyncStatus = "error"
    connection.lastSyncError = message[:500]
    connection.updatedAt = utcnow()
    session.commit()


def execute_sync(session: Session, clerk_id: str, settings: Settings) -> SyncStats:
    """Refresh tokens, call Gmail, and import. Used by the HTTP routes."""
    from app.gmail.oauth import (
        build_api_client,
        credentials_from_connection,
        persist_refreshed_credentials,
    )

    connection = session.scalar(select(GmailConnection).where(GmailConnection.clerkId == clerk_id))
    if connection is None:
        raise GmailNotConnected(clerk_id)
    creds = credentials_from_connection(connection, settings)
    persist_refreshed_credentials(session, connection, creds, settings)
    client = build_api_client(creds)
    return sync_connection(session, connection, client, settings, LLMClassifier(settings))


def sync_all(settings: Settings) -> list[dict]:
    from app.db import create_session

    session = create_session()
    if session is None:
        raise RuntimeError("DATABASE_URL is not configured")
    try:
        clerk_ids = [row.clerkId for row in session.scalars(select(GmailConnection)).all()]
    finally:
        session.close()

    results = []
    for clerk_id in clerk_ids:
        session = create_session()
        try:
            stats = execute_sync(session, clerk_id, settings)
            results.append({"clerkId": clerk_id, "ok": True, **stats.as_dict()})
        except Exception as error:
            logger.exception("sync failed for %s", clerk_id)
            session.rollback()
            mark_sync_error(session, clerk_id, safe_error_text(error))
            results.append({"clerkId": clerk_id, "ok": False})
        finally:
            session.close()
    return results
