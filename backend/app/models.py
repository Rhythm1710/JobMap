from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Index, String, Text, UniqueConstraint

from app.db import Base

GMAIL_READONLY = "https://www.googleapis.com/auth/gmail.readonly"


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Job(Base):
    __tablename__ = "Job"

    id = Column(String, primary_key=True)
    clerkId = Column(String, nullable=False)
    createdAt = Column(DateTime, nullable=False, default=utcnow)
    updatedAt = Column(DateTime, nullable=False, default=utcnow)
    position = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=False)
    status = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    source = Column(String, nullable=False, default="manual")
    gmailMessageId = Column(String, nullable=True)
    gmailThreadId = Column(String, nullable=True)
    appliedAt = Column(DateTime, nullable=True)
    jobUrl = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    companyKey = Column(String, nullable=False, default="")
    roleKey = Column(String, nullable=False, default="")
    manuallyEdited = Column(Boolean, nullable=False, default=False)
    # True when the owner picked the status. Auto-ghost will not overwrite it.
    statusManual = Column(Boolean, nullable=False, default=False)

    __table_args__ = (
        UniqueConstraint("clerkId", "gmailThreadId", name="Job_clerkId_gmailThreadId_key"),
        Index("Job_clerkId_companyKey_roleKey_idx", "clerkId", "companyKey", "roleKey"),
        Index("Job_clerkId_status_idx", "clerkId", "status"),
    )


class GmailConnection(Base):
    __tablename__ = "GmailConnection"

    id = Column(String, primary_key=True)
    clerkId = Column(String, nullable=False, unique=True)
    email = Column(String, nullable=True)
    accessTokenEnc = Column(Text, nullable=False)
    refreshTokenEnc = Column(Text, nullable=False)
    tokenExpiry = Column(DateTime, nullable=True)
    scopes = Column(String, nullable=False, default=GMAIL_READONLY)
    historyId = Column(String, nullable=True)
    backfillBefore = Column(DateTime, nullable=True)
    backfillComplete = Column(Boolean, nullable=False, default=False)
    lastSyncedAt = Column(DateTime, nullable=True)
    lastSyncStatus = Column(String, nullable=True)
    lastSyncError = Column(Text, nullable=True)
    createdAt = Column(DateTime, nullable=False, default=utcnow)
    updatedAt = Column(DateTime, nullable=False, default=utcnow)


class GmailMessage(Base):
    __tablename__ = "GmailMessage"

    id = Column(String, primary_key=True)
    clerkId = Column(String, nullable=False)
    gmailMessageId = Column(String, nullable=False)
    gmailThreadId = Column(String, nullable=False)
    jobId = Column(String, ForeignKey("Job.id", ondelete="SET NULL"), nullable=True)
    disposition = Column(String, nullable=False)
    statusHint = Column(String, nullable=True)
    subject = Column(String, nullable=True)
    receivedAt = Column(DateTime, nullable=True)
    createdAt = Column(DateTime, nullable=False, default=utcnow)

    __table_args__ = (
        UniqueConstraint("clerkId", "gmailMessageId", name="GmailMessage_clerkId_gmailMessageId_key"),
        Index("GmailMessage_clerkId_gmailThreadId_idx", "clerkId", "gmailThreadId"),
    )
