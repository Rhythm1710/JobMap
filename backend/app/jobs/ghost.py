"""Mark applications ghosted when nobody has written back.

Only `applied` and `assessment` are eligible, and only when the owner has not
set the status themselves (`statusManual`). A later email replaces `ghosted`
through merge_status, which does not treat ghosted as sticky.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.jobs.upsert import append_note
from app.models import GmailMessage, Job, utcnow

GHOSTABLE = {"applied", "assessment"}


@dataclass
class GhostCandidate:
    id: str
    status: str
    status_manual: bool
    activity_at: datetime | None


def select_ghosts(candidates: list[GhostCandidate], now: datetime, days: int) -> list[str]:
    if days <= 0:
        return []
    cutoff = now - timedelta(days=days)
    chosen: list[str] = []
    for job in candidates:
        if job.status_manual or job.status not in GHOSTABLE:
            continue
        if job.activity_at is None or job.activity_at > cutoff:
            continue
        chosen.append(job.id)
    return chosen


def apply_ghosting(session: Session, clerk_id: str, now: datetime | None = None, days: int = 30) -> int:
    """Ghost this user's silent applications. Returns how many rows changed."""
    if days <= 0:
        return 0
    moment = now or utcnow()
    session.flush()
    jobs = session.scalars(select(Job).where(Job.clerkId == clerk_id)).all()
    messages = session.scalars(
        select(GmailMessage).where(GmailMessage.clerkId == clerk_id, GmailMessage.jobId.is_not(None))
    ).all()
    last_email: dict[str, datetime] = {}
    for message in messages:
        if not message.jobId or message.receivedAt is None:
            continue
        current = last_email.get(message.jobId)
        if current is None or message.receivedAt > current:
            last_email[message.jobId] = message.receivedAt
    candidates = [
        GhostCandidate(
            id=job.id,
            status=job.status,
            status_manual=bool(job.statusManual),
            activity_at=last_email.get(job.id) or job.appliedAt or job.createdAt,
        )
        for job in jobs
    ]
    chosen = set(select_ghosts(candidates, moment, days))
    changed = 0
    for job in jobs:
        if job.id not in chosen:
            continue
        job.status = "ghosted"
        job.notes = append_note(job.notes, moment, "ghosted", f"no email for {days} days")
        job.updatedAt = moment
        changed += 1
    return changed
