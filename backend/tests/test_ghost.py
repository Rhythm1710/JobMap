from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base
from app.gmail.sync import sync_connection
from app.jobs.ghost import GhostCandidate, apply_ghosting, select_ghosts
from app.jobs.upsert import KnownJob, UserState, plan_decision
from app.models import GmailConnection, GmailMessage, Job, utcnow
from tests.fixtures import gmail_payload
from tests.test_sync import FakeGmail, _connection, _settings
from tests.test_upsert import _email


NOW = datetime(2026, 11, 11, 12, 0, 0)


def _candidate(status: str, days_silent: int, manual: bool = False) -> GhostCandidate:
    return GhostCandidate(
        id=f"{status}-{days_silent}-{manual}",
        status=status,
        status_manual=manual,
        activity_at=NOW - timedelta(days=days_silent),
    )


def test_select_ghosts_only_silent_applied_and_assessment_rows():
    candidates = [
        _candidate("applied", 31),
        _candidate("assessment", 30),
        _candidate("applied", 29),
        _candidate("interview", 90),
        _candidate("offer", 90),
        _candidate("rejected", 90),
        _candidate("applied", 60, manual=True),
        _candidate("assessment", 60, manual=True),
    ]
    chosen = select_ghosts(candidates, NOW, 30)
    assert chosen == ["applied-31-False", "assessment-30-False"]
    assert select_ghosts(candidates, NOW, 0) == []


def test_a_later_email_moves_a_ghosted_job_to_that_email_status():
    state = UserState(
        jobs=[
            KnownJob(
                id="job-1",
                company_key="stripe",
                role_key="backend engineer",
                status="ghosted",
                source="gmail",
                gmail_thread_id="t1",
                thread_ids={"t1"},
                company="Stripe",
                position="Backend Engineer",
                applied_at=NOW - timedelta(days=45),
            )
        ]
    )
    decision = plan_decision(state, _email("m2", "t1", "interview", day=2), "user_1")
    assert decision.changes["status"] == "interview"


def _session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


def test_apply_ghosting_uses_the_latest_email_and_skips_manual_status():
    session = _session()
    old = NOW - timedelta(days=40)
    recent = NOW - timedelta(days=3)
    now = utcnow()
    session.add_all(
        [
            Job(
                id="silent",
                clerkId="user_1",
                createdAt=old,
                updatedAt=old,
                position="Backend Engineer",
                company="Stripe",
                location="Remote",
                status="applied",
                mode="full-time",
                source="gmail",
                appliedAt=old,
                companyKey="stripe",
                roleKey="backend engineer",
                manuallyEdited=False,
                statusManual=False,
            ),
            Job(
                id="fresh",
                clerkId="user_1",
                createdAt=recent,
                updatedAt=recent,
                position="Designer",
                company="Figma",
                location="Remote",
                status="assessment",
                mode="full-time",
                source="gmail",
                appliedAt=recent,
                companyKey="figma",
                roleKey="designer",
                manuallyEdited=False,
                statusManual=False,
            ),
            Job(
                id="locked",
                clerkId="user_1",
                createdAt=old,
                updatedAt=old,
                position="PM",
                company="Notion",
                location="Remote",
                status="applied",
                mode="full-time",
                source="manual",
                appliedAt=old,
                companyKey="notion",
                roleKey="pm",
                manuallyEdited=False,
                statusManual=True,
            ),
        ]
    )
    session.add(
        GmailMessage(
            id="msg-1",
            clerkId="user_1",
            gmailMessageId="m-old",
            gmailThreadId="t-old",
            jobId="silent",
            disposition="created",
            receivedAt=old,
            createdAt=now,
        )
    )
    session.commit()
    changed = apply_ghosting(session, "user_1", NOW, 30)
    session.commit()
    assert changed == 1
    assert session.get(Job, "silent").status == "ghosted"
    assert "ghosted" in (session.get(Job, "silent").notes or "")
    assert session.get(Job, "fresh").status == "assessment"
    assert session.get(Job, "locked").status == "applied"
    session.close()


def test_sync_ghosts_an_old_application(db):
    connection = _connection()
    db.add(connection)
    db.commit()
    received = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(days=45)
    message = gmail_payload(
        "m-old",
        "thread-old",
        "Thank you for applying to Stripe",
        "We received your application for the Backend Engineer role at Stripe.",
        "Stripe <no-reply@greenhouse-mail.io>",
        received,
    )
    settings = _settings()
    settings.ghost_after_days = 30
    sync_connection(db, connection, FakeGmail([message]), settings, llm=None)
    job = db.scalar(select(Job).where(Job.clerkId == "user_1"))
    assert job is not None
    assert job.status == "ghosted"
    assert job.statusManual is False
