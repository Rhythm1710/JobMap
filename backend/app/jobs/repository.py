"""Apply upsert decisions to the Prisma tables."""

from __future__ import annotations

from collections import defaultdict
from uuid import uuid4

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.jobs.normalize import normalize_key, normalize_role
from app.jobs.upsert import (
    Create,
    Defer,
    Ignore,
    Incoming,
    KnownJob,
    Skip,
    Update,
    UserState,
)
from app.models import GmailMessage, Job, utcnow


def backfill_keys(session: Session) -> int:
    """Fill empty company/role keys from the current text. Idempotent."""
    rows = session.scalars(select(Job).where(or_(Job.companyKey == "", Job.roleKey == ""))).all()
    changed = 0
    for job in rows:
        company_key = normalize_key(job.company)
        role_key = normalize_role(job.position)
        if job.companyKey != company_key or job.roleKey != role_key:
            job.companyKey = company_key
            job.roleKey = role_key
            job.updatedAt = utcnow()
            changed += 1
    return changed


def load_user_state(session: Session, clerk_id: str) -> UserState:
    jobs = session.scalars(select(Job).where(Job.clerkId == clerk_id)).all()
    messages = session.scalars(select(GmailMessage).where(GmailMessage.clerkId == clerk_id)).all()
    threads_by_job: dict[str, set[str]] = defaultdict(set)
    seen: set[str] = set()
    deferred: set[str] = set()
    for message in messages:
        if message.disposition == "deferred":
            deferred.add(message.gmailMessageId)
        else:
            seen.add(message.gmailMessageId)
        if message.jobId and message.gmailThreadId:
            threads_by_job[message.jobId].add(message.gmailThreadId)
    known: list[KnownJob] = []
    for job in jobs:
        threads = set(threads_by_job.get(job.id, set()))
        if job.gmailThreadId:
            threads.add(job.gmailThreadId)
        known.append(
            KnownJob(
                id=job.id,
                company_key=job.companyKey or "",
                role_key=job.roleKey or "",
                status=job.status,
                source=job.source,
                gmail_thread_id=job.gmailThreadId,
                thread_ids=threads,
                manually_edited=bool(job.manuallyEdited),
                applied_at=job.appliedAt,
                position=job.position,
                company=job.company,
                location=job.location,
                mode=job.mode,
                job_url=job.jobUrl,
                notes=job.notes,
                gmail_message_id=job.gmailMessageId,
            )
        )
    return UserState(jobs=known, seen_message_ids=seen, deferred_message_ids=deferred)


def _upsert_message(
    session: Session,
    clerk_id: str,
    incoming: Incoming,
    *,
    disposition: str,
    job_id: str | None,
    status_hint: str | None,
) -> None:
    existing = session.scalar(
        select(GmailMessage).where(
            GmailMessage.clerkId == clerk_id,
            GmailMessage.gmailMessageId == incoming.message_id,
        )
    )
    subject = (incoming.subject or "")[:500] or None
    if existing is None:
        session.add(
            GmailMessage(
                id=str(uuid4()),
                clerkId=clerk_id,
                gmailMessageId=incoming.message_id,
                gmailThreadId=incoming.thread_id,
                jobId=job_id,
                disposition=disposition,
                statusHint=status_hint,
                subject=subject,
                receivedAt=incoming.received_at,
                createdAt=utcnow(),
            )
        )
        return
    existing.disposition = disposition
    existing.jobId = job_id
    existing.gmailThreadId = incoming.thread_id
    existing.statusHint = status_hint
    existing.subject = subject
    existing.receivedAt = incoming.received_at


def _apply_changes(row: Job, changes: dict) -> None:
    mapping = {
        "position": "position",
        "company": "company",
        "location": "location",
        "status": "status",
        "mode": "mode",
        "job_url": "jobUrl",
        "notes": "notes",
        "company_key": "companyKey",
        "role_key": "roleKey",
        "applied_at": "appliedAt",
        "gmail_thread_id": "gmailThreadId",
        "gmail_message_id": "gmailMessageId",
        "manually_edited": "manuallyEdited",
    }
    for key, value in changes.items():
        column = mapping.get(key)
        if column is None:
            continue
        setattr(row, column, value)
    row.updatedAt = utcnow()


def apply_decision(session: Session, clerk_id: str, decision, incoming: Incoming) -> str:
    """Persist one decision. Returns the disposition recorded for the message."""
    hint = incoming.extraction.status
    if isinstance(decision, Skip):
        return "skipped"
    if isinstance(decision, Ignore):
        _upsert_message(
            session, clerk_id, incoming, disposition="ignored", job_id=None, status_hint=decision.reason[:120]
        )
        return "ignored"
    if isinstance(decision, Defer):
        _upsert_message(
            session, clerk_id, incoming, disposition="deferred", job_id=None, status_hint=decision.reason[:120]
        )
        return "deferred"
    if isinstance(decision, Create):
        job = decision.job
        now = utcnow()
        session.add(
            Job(
                id=job["id"],
                clerkId=clerk_id,
                createdAt=now,
                updatedAt=now,
                position=job["position"],
                company=job["company"],
                location=job["location"],
                status=job["status"],
                mode=job["mode"],
                source="gmail",
                gmailMessageId=job["gmail_message_id"],
                gmailThreadId=job["gmail_thread_id"],
                appliedAt=job["applied_at"],
                jobUrl=job["job_url"],
                notes=job["notes"],
                companyKey=job["company_key"],
                roleKey=job["role_key"],
                manuallyEdited=False,
            )
        )
        _upsert_message(
            session,
            clerk_id,
            incoming,
            disposition="created",
            job_id=job["id"],
            status_hint=hint,
        )
        return "created"
    if isinstance(decision, Update):
        row = session.get(Job, decision.job_id)
        if row is None or row.clerkId != clerk_id:
            _upsert_message(
                session,
                clerk_id,
                incoming,
                disposition="deferred",
                job_id=None,
                status_hint="matched job missing",
            )
            return "deferred"
        if decision.changes:
            _apply_changes(row, decision.changes)
        _upsert_message(
            session,
            clerk_id,
            incoming,
            disposition="linked",
            job_id=row.id,
            status_hint=hint,
        )
        return "linked"
    raise TypeError(f"unknown decision {type(decision)!r}")


def record_message_gone(session: Session, clerk_id: str, message_id: str, thread_id: str = "") -> None:
    """Stop retrying a Gmail id that no longer exists."""
    now = utcnow()
    existing = session.scalar(
        select(GmailMessage).where(
            GmailMessage.clerkId == clerk_id,
            GmailMessage.gmailMessageId == message_id,
        )
    )
    if existing is None:
        session.add(
            GmailMessage(
                id=str(uuid4()),
                clerkId=clerk_id,
                gmailMessageId=message_id,
                gmailThreadId=thread_id or message_id,
                jobId=None,
                disposition="ignored",
                statusHint="message gone",
                subject=None,
                receivedAt=now,
                createdAt=now,
            )
        )
        return
    existing.disposition = "ignored"
    existing.statusHint = "message gone"
