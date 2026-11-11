from datetime import datetime, timedelta

from app.jobs.upsert import (
    Create,
    Defer,
    Extraction,
    Ignore,
    Incoming,
    KnownJob,
    Skip,
    Update,
    UserState,
    fold_state,
    merge_status,
    plan_decision,
)


def _email(
    message_id: str,
    thread_id: str,
    status: str,
    company: str = "Stripe",
    position: str = "Backend Engineer",
    day: int = 1,
    is_application: bool = True,
    needs_review: bool = False,
) -> Incoming:
    return Incoming(
        message_id=message_id,
        thread_id=thread_id,
        received_at=datetime(2026, 1, day, 12, 0, 0),
        subject=f"{status} at {company}",
        sender=f"{company} <jobs@{company.lower()}.com>",
        extraction=Extraction(
            is_application=is_application,
            company=company,
            position=position,
            status=status,
            confidence=0.9,
            needs_review=needs_review,
        ),
    )


def test_status_does_not_regress_and_offer_sticks():
    assert merge_status("applied", "interview") == "interview"
    assert merge_status("interview", "applied") == "interview"
    assert merge_status("assessment", "interview") == "assessment"
    assert merge_status("applied", "rejected") == "rejected"
    assert merge_status("rejected", "interview") == "interview"
    assert merge_status("offer", "rejected") == "offer"
    assert merge_status("rejected", "offer") == "offer"
    assert merge_status("ghosted", "interview") == "ghosted"
    assert merge_status("ghosted", "offer") == "offer"
    assert merge_status("withdrawn", "rejected") == "withdrawn"


def test_same_thread_and_same_company_role_update_one_job():
    state = UserState()
    first = plan_decision(state, _email("m1", "t1", "applied", day=1), "user_1")
    assert isinstance(first, Create)
    fold_state(state, first, _email("m1", "t1", "applied", day=1))

    second = plan_decision(state, _email("m2", "t1", "interview", day=2), "user_1")
    assert isinstance(second, Update)
    assert second.job_id == first.job["id"]
    assert second.changes["status"] == "interview"
    fold_state(state, second, _email("m2", "t1", "interview", day=2))

    third = plan_decision(state, _email("m1", "t1", "applied", day=1), "user_1")
    assert isinstance(third, Skip)

    fourth = plan_decision(state, _email("m3", "t-other", "rejected", day=3), "user_1")
    assert isinstance(fourth, Update)
    assert fourth.job_id == first.job["id"]
    assert fourth.changes["status"] == "rejected"
    fold_state(state, fourth, _email("m3", "t-other", "rejected", day=3))

    offer = plan_decision(state, _email("m4", "t-offer", "offer", day=4), "user_1")
    assert isinstance(offer, Update)
    assert offer.changes["status"] == "offer"
    fold_state(state, offer, _email("m4", "t-offer", "offer", day=4))

    late_rejection = plan_decision(state, _email("m5", "t-late", "rejected", day=5), "user_1")
    assert isinstance(late_rejection, Update)
    assert "status" not in late_rejection.changes

    other_role = plan_decision(
        state,
        _email("m6", "t-role", "applied", position="Product Designer", day=6),
        "user_1",
    )
    assert isinstance(other_role, Create)
    assert len(state.jobs) == 1  # fold happens after; the new job is not the same id
    fold_state(state, other_role, _email("m6", "t-role", "applied", position="Product Designer", day=6))
    assert len(state.jobs) == 2
    assert {job.role_key for job in state.jobs} == {"backend engineer", "product designer"}


def test_manual_edits_keep_identity_but_status_can_advance():
    state = UserState(
        jobs=[
            KnownJob(
                id="job-manual",
                company_key="stripe",
                role_key="backend engineer",
                status="applied",
                source="manual",
                gmail_thread_id=None,
                company="Stripe",
                position="Backend Engineer",
                location="Remote",
                manually_edited=True,
                applied_at=datetime(2025, 12, 1),
                notes="wrote this myself",
            )
        ]
    )
    decision = plan_decision(
        state,
        _email("m9", "thread-9", "interview", company="Stripe Inc.", day=9),
        "user_1",
    )
    assert isinstance(decision, Update)
    assert decision.job_id == "job-manual"
    assert decision.changes["status"] == "interview"
    assert "company" not in decision.changes
    assert "position" not in decision.changes
    assert "applied_at" not in decision.changes


def test_unrelated_and_incomplete_mail_do_not_create_jobs():
    state = UserState()
    newsletter = Incoming(
        message_id="n1",
        thread_id="tn",
        received_at=datetime(2026, 1, 2),
        subject="This week in tech",
        sender="news@tldr.tech",
        extraction=Extraction(is_application=False, confidence=0.9, needs_review=False),
    )
    assert isinstance(plan_decision(state, newsletter, "user_1"), Ignore)

    ambiguous = Incoming(
        message_id="n2",
        thread_id="ta",
        received_at=datetime(2026, 1, 3),
        subject="hiring",
        sender="a@b.c",
        extraction=Extraction(is_application=False, confidence=0.35, needs_review=True, reason="weak"),
    )
    assert isinstance(plan_decision(state, ambiguous, "user_1"), Defer)

    half = _email("n3", "th", "applied", company="Stripe", position="", day=4)
    half.extraction.position = None
    assert isinstance(plan_decision(state, half, "user_1"), Defer)


def test_applied_at_is_preserved_when_already_set():
    existing = KnownJob(
        id="j",
        company_key="stripe",
        role_key="backend engineer",
        status="applied",
        source="gmail",
        gmail_thread_id="t1",
        thread_ids={"t1"},
        applied_at=datetime(2026, 1, 1),
        company="Stripe",
        position="Backend Engineer",
    )
    state = UserState(jobs=[existing])
    decision = plan_decision(state, _email("m2", "t1", "interview", day=20), "user_1")
    assert isinstance(decision, Update)
    assert "applied_at" not in decision.changes
    assert decision.changes["notes"].startswith("[2026-01-20] interview")


def test_empty_role_does_not_merge_two_unknowns_at_one_company():
    state = UserState(
        jobs=[
            KnownJob(
                id="j",
                company_key="stripe",
                role_key="",
                status="applied",
                source="gmail",
                gmail_thread_id="t-old",
                company="Stripe",
                position="",
            )
        ]
    )
    email = _email("m", "t-new", "interview", company="Stripe", position="Data Scientist")
    # Different role key, and the stored job has no role key, so this is a new application.
    decision = plan_decision(state, email, "user_1")
    assert isinstance(decision, Create)
    assert state.jobs[0].applied_at is None or decision.job["applied_at"] > (
        state.jobs[0].applied_at or datetime.min
    )
