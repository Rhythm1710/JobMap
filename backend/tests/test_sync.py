from datetime import datetime

from app.config import Settings
from app.gmail.client import HistoryExpired, HistoryPage, MessageGone, MessagePage
from app.gmail.sync import sync_connection
from app.models import GmailConnection, GmailMessage, Job, utcnow
from tests.fixtures import gmail_payload


class FakeGmail:
    def __init__(self, messages, history_expired=False, history_ids=None):
        self.messages = {message["id"]: message for message in messages}
        self.history_expired = history_expired
        self.history_ids = list(history_ids or [])
        self.profile = {"emailAddress": "ada@example.com", "historyId": "55"}

    def get_profile(self):
        return self.profile

    def list_history(self, start_history_id: str, limit: int) -> HistoryPage:
        if self.history_expired:
            raise HistoryExpired("expired")
        return HistoryPage(message_ids=self.history_ids[:limit], latest_history_id="56")

    def list_messages(self, query: str, limit: int) -> MessagePage:
        ids = list(self.messages)[:limit]
        return MessagePage(ids=ids, exhausted=len(self.messages) <= limit)

    def get_message(self, message_id: str) -> dict:
        if message_id not in self.messages:
            raise MessageGone(message_id)
        return self.messages[message_id]


def _settings() -> Settings:
    return Settings(
        service_secret="test-secret",
        gmail_lookback_days=180,
        gmail_max_messages_per_run=50,
        llm_api_key="",
    )


def _connection() -> GmailConnection:
    now = utcnow()
    return GmailConnection(
        id="conn-1",
        clerkId="user_1",
        email=None,
        accessTokenEnc="enc-access",
        refreshTokenEnc="enc-refresh",
        tokenExpiry=None,
        scopes="https://www.googleapis.com/auth/gmail.readonly",
        historyId=None,
        backfillBefore=None,
        backfillComplete=False,
        lastSyncedAt=None,
        lastSyncStatus=None,
        lastSyncError=None,
        createdAt=now,
        updatedAt=now,
    )


def _messages():
    start = datetime(2026, 4, 1, 15, 0, 0)
    applied = gmail_payload(
        "m-applied",
        "thread-stripe",
        "Thank you for applying to Stripe",
        "We received your application for the Backend Engineer role at Stripe.",
        "Stripe <no-reply@greenhouse-mail.io>",
        start,
    )
    interview = gmail_payload(
        "m-interview",
        "thread-stripe",
        "Interview invitation — Stripe / Backend Engineer",
        "We would like to schedule a phone screen.",
        "Stripe <talent@stripe.com>",
        datetime(2026, 4, 8, 15, 0, 0),
    )
    rejection = gmail_payload(
        "m-reject",
        "thread-other",
        "Update on your Stripe application",
        "Thank you for your interest in the Backend Engineer position at Stripe. "
        "Unfortunately, we have decided not to move forward.",
        "Stripe Careers <no-reply@lever.co>",
        datetime(2026, 4, 20, 15, 0, 0),
    )
    newsletter = gmail_payload(
        "m-news",
        "thread-news",
        "This week in tech",
        "Top stories: a startup raised a series B. No action needed.",
        "TLDR <news@tldr.tech>",
        datetime(2026, 4, 2, 15, 0, 0),
    )
    return [rejection, newsletter, applied, interview]


def test_sync_groups_threads_and_is_idempotent(db):
    connection = _connection()
    db.add(connection)
    db.commit()
    client = FakeGmail(_messages())

    first = sync_connection(db, connection, client, _settings(), llm=None)
    assert first.created == 1
    assert first.updated == 2  # interview, then rejection, same application
    assert first.ignored == 1

    jobs = db.query(Job).filter_by(clerkId="user_1").all()
    assert len(jobs) == 1
    job = jobs[0]
    assert job.company == "Stripe"
    assert job.position == "Backend Engineer"
    assert job.status == "rejected"
    assert job.source == "gmail"
    assert job.gmailThreadId == "thread-stripe"
    assert job.appliedAt == datetime(2026, 4, 1, 15, 0, 0)
    assert "interview" in (job.notes or "")
    assert "rejected" in (job.notes or "")

    messages = db.query(GmailMessage).filter_by(clerkId="user_1").all()
    assert {message.gmailMessageId for message in messages} == {
        "m-applied",
        "m-interview",
        "m-reject",
        "m-news",
    }
    assert connection.backfillComplete is True
    assert connection.historyId == "55"
    assert connection.lastSyncStatus == "ok"
    assert connection.email == "ada@example.com"

    replay = FakeGmail(_messages(), history_ids=["m-applied", "m-interview", "m-reject", "m-news"])
    second = sync_connection(db, connection, replay, _settings(), llm=None)
    assert second.created == 0
    assert second.updated == 0
    assert second.skipped == 4
    assert db.query(Job).filter_by(clerkId="user_1").count() == 1


def test_sync_updates_a_manual_job_without_replacing_it(db):
    now = utcnow()
    db.add(
        Job(
            id="manual-1",
            clerkId="user_1",
            createdAt=now,
            updatedAt=now,
            position="Backend Engineer",
            company="Stripe, Inc.",
            location="Remote",
            status="applied",
            mode="full-time",
            source="manual",
            appliedAt=datetime(2026, 3, 1, 0, 0, 0),
            companyKey="",
            roleKey="",
            manuallyEdited=False,
        )
    )
    connection = _connection()
    db.add(connection)
    db.commit()

    message = gmail_payload(
        "m-reject",
        "thread-new",
        "Update on your application",
        "Thank you for your interest in the Backend Engineer position at Stripe. "
        "Unfortunately, we have decided not to move forward.",
        "Stripe <jobs@stripe.com>",
        datetime(2026, 4, 2, 12, 0, 0),
    )
    stats = sync_connection(db, connection, FakeGmail([message]), _settings(), llm=None)
    assert stats.created == 0
    assert stats.updated == 1
    job = db.get(Job, "manual-1")
    assert job.status == "rejected"
    assert job.source == "manual"
    assert job.company == "Stripe, Inc."
    assert job.appliedAt == datetime(2026, 3, 1, 0, 0, 0)
    assert db.query(Job).count() == 1


def test_a_failed_message_does_not_advance_the_cursor(db):
    connection = _connection()
    db.add(connection)
    db.commit()

    class Flaky(FakeGmail):
        def get_message(self, message_id: str) -> dict:
            if message_id == "m-applied":
                raise RuntimeError("temporary gmail failure")
            return super().get_message(message_id)

    stats = sync_connection(db, connection, Flaky(_messages()), _settings(), llm=None)
    assert stats.errors == 1
    assert connection.historyId is None
    assert connection.backfillComplete is False
    assert connection.lastSyncStatus == "partial"
    assert db.query(GmailMessage).filter_by(gmailMessageId="m-applied").count() == 0


def test_deleted_gmail_message_is_not_retried(db):
    connection = _connection()
    db.add(connection)
    db.commit()

    class Missing(FakeGmail):
        def list_messages(self, query: str, limit: int) -> MessagePage:
            return MessagePage(ids=["gone-1"], exhausted=True)

        def get_message(self, message_id: str) -> dict:
            raise MessageGone(message_id)

    first = sync_connection(db, connection, Missing([]), _settings(), llm=None)
    assert first.ignored == 1
    row = db.query(GmailMessage).filter_by(gmailMessageId="gone-1").one()
    assert row.disposition == "ignored"
    second = sync_connection(db, connection, Missing([]), _settings(), llm=None)
    assert second.errors == 0
    assert second.ignored == 0
    assert db.query(GmailMessage).filter_by(gmailMessageId="gone-1").count() == 1
