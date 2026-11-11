"""Pure grouping and status-merge decisions.

The database adapter in repository.py applies these decisions. Tests exercise
this module without Postgres so dedup behavior stays explicit.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import uuid4

from app.jobs.normalize import normalize_key, normalize_role

# Offer sticks. Rejected can be overwritten by a later interview, assessment, or offer
# (a pipeline sometimes reopens). Ghosted and withdrawn are manual and stay put
# unless an offer arrives. Assessment outranks a bare interview mention so an
# online-assessment email that also says "interview" stays an assessment.
_RANK = {
    "applied": 1,
    "interview": 2,
    "assessment": 3,
    "offer": 4,
}
_MANUAL_STICKY = {"ghosted", "withdrawn"}
_REOPEN = {"assessment", "interview", "offer"}


def merge_status(current: str | None, new: str | None) -> str | None:
    if not new or new == current:
        return current
    if current == "offer":
        return current
    if current in _MANUAL_STICKY:
        return "offer" if new == "offer" else current
    if new == "rejected":
        return "rejected"
    if current == "rejected":
        return new if new in _REOPEN else current
    if _RANK.get(new, 0) > _RANK.get(current or "", 0):
        return new
    return current


def append_note(existing: str | None, when: datetime, status: str, subject: str) -> str:
    line = f"[{when.date().isoformat()}] {status} — {subject.strip()[:180]}"
    if existing and line in existing:
        return existing
    parts = [part for part in (existing or "").splitlines() if part.strip()]
    parts.append(line)
    return "\n".join(parts[-20:])


@dataclass
class Extraction:
    is_application: bool
    company: str | None = None
    position: str | None = None
    status: str | None = None
    location: str | None = None
    mode: str | None = None
    job_url: str | None = None
    confidence: float = 0.0
    needs_review: bool = False
    reason: str = ""


@dataclass
class Incoming:
    message_id: str
    thread_id: str
    received_at: datetime
    subject: str
    sender: str
    extraction: Extraction


@dataclass
class KnownJob:
    id: str
    company_key: str
    role_key: str
    status: str
    source: str
    gmail_thread_id: str | None
    thread_ids: set[str] = field(default_factory=set)
    manually_edited: bool = False
    applied_at: datetime | None = None
    position: str = ""
    company: str = ""
    location: str = ""
    mode: str = "full-time"
    job_url: str | None = None
    notes: str | None = None
    gmail_message_id: str | None = None


@dataclass
class UserState:
    jobs: list[KnownJob] = field(default_factory=list)
    seen_message_ids: set[str] = field(default_factory=set)
    deferred_message_ids: set[str] = field(default_factory=set)


@dataclass
class Skip:
    reason: str


@dataclass
class Ignore:
    reason: str


@dataclass
class Defer:
    reason: str


@dataclass
class Create:
    job: dict


@dataclass
class Update:
    job_id: str
    changes: dict


Decision = Skip | Ignore | Defer | Create | Update


def find_match(state: UserState, incoming: Incoming) -> KnownJob | None:
    thread = incoming.thread_id
    for job in state.jobs:
        if job.gmail_thread_id == thread or thread in job.thread_ids:
            return job
    company_key = normalize_key(incoming.extraction.company)
    role_key = normalize_role(incoming.extraction.position)
    # An empty role must not glue unrelated applications at the same company together.
    if not company_key or not role_key:
        return None
    candidates = [
        job for job in state.jobs if job.company_key == company_key and job.role_key == role_key
    ]
    if not candidates:
        return None
    candidates.sort(key=lambda job: job.applied_at or datetime.min, reverse=True)
    return candidates[0]


def build_patch(job: KnownJob, incoming: Incoming) -> dict:
    """Fields a later email may change. Identity fields stay after the first good extract."""
    changes: dict = {}
    merged = merge_status(job.status, incoming.extraction.status)
    if merged and merged != job.status:
        changes["status"] = merged
        changes["notes"] = append_note(job.notes, incoming.received_at, merged, incoming.subject)
    if not job.applied_at:
        changes["applied_at"] = incoming.received_at
    if not job.gmail_thread_id:
        changes["gmail_thread_id"] = incoming.thread_id
    if job.manually_edited:
        return changes

    extraction = incoming.extraction
    if not job.company_key and extraction.company:
        changes["company"] = extraction.company
        changes["company_key"] = normalize_key(extraction.company)
    if not job.role_key and extraction.position:
        changes["position"] = extraction.position
        changes["role_key"] = normalize_role(extraction.position)
    if extraction.location and (not job.location or job.location == "Unspecified"):
        changes["location"] = extraction.location
    if job.mode == "full-time" and extraction.mode and extraction.mode != "full-time":
        changes["mode"] = extraction.mode
    if not job.job_url and extraction.job_url:
        changes["job_url"] = extraction.job_url
    return changes


def _new_job(clerk_id: str, incoming: Incoming) -> dict:
    extraction = incoming.extraction
    company = extraction.company or "Unknown company"
    position = extraction.position or "Unknown role"
    status = extraction.status or "applied"
    return {
        "id": str(uuid4()),
        "clerk_id": clerk_id,
        "position": position,
        "company": company,
        "location": extraction.location or "Unspecified",
        "status": status,
        "mode": extraction.mode or "full-time",
        "source": "gmail",
        "gmail_message_id": incoming.message_id,
        "gmail_thread_id": incoming.thread_id,
        "applied_at": incoming.received_at,
        "job_url": extraction.job_url,
        "notes": append_note(None, incoming.received_at, status, incoming.subject),
        "company_key": normalize_key(company),
        "role_key": normalize_role(position),
        "manually_edited": False,
    }


def plan_decision(state: UserState, incoming: Incoming, clerk_id: str) -> Decision:
    if incoming.message_id in state.seen_message_ids:
        return Skip("already processed")
    extraction = incoming.extraction
    if not extraction.is_application:
        if extraction.needs_review:
            return Defer(extraction.reason or "ambiguous")
        return Ignore(extraction.reason or "not an application")
    match = find_match(state, incoming)
    if match is None:
        if not (extraction.company and extraction.position and extraction.status):
            return Defer("incomplete extraction")
        return Create(job=_new_job(clerk_id, incoming))
    return Update(job_id=match.id, changes=build_patch(match, incoming))


def fold_state(state: UserState, decision: Decision, incoming: Incoming) -> UserState:
    """Apply a decision to the in-memory snapshot so later mail in the same run dedups."""
    if isinstance(decision, Skip):
        return state
    if isinstance(decision, Defer):
        state.deferred_message_ids.add(incoming.message_id)
        return state
    if isinstance(decision, Ignore):
        state.seen_message_ids.add(incoming.message_id)
        state.deferred_message_ids.discard(incoming.message_id)
        return state
    if isinstance(decision, Create):
        job = decision.job
        state.jobs.append(
            KnownJob(
                id=job["id"],
                company_key=job["company_key"],
                role_key=job["role_key"],
                status=job["status"],
                source=job["source"],
                gmail_thread_id=job["gmail_thread_id"],
                thread_ids={job["gmail_thread_id"]},
                manually_edited=False,
                applied_at=job["applied_at"],
                position=job["position"],
                company=job["company"],
                location=job["location"],
                mode=job["mode"],
                job_url=job["job_url"],
                notes=job["notes"],
                gmail_message_id=job["gmail_message_id"],
            )
        )
        state.seen_message_ids.add(incoming.message_id)
        state.deferred_message_ids.discard(incoming.message_id)
        return state
    target = next(job for job in state.jobs if job.id == decision.job_id)
    for key, value in decision.changes.items():
        setattr(target, key, value)
    if incoming.thread_id:
        target.thread_ids.add(incoming.thread_id)
    state.seen_message_ids.add(incoming.message_id)
    state.deferred_message_ids.discard(incoming.message_id)
    return state
