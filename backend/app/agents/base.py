"""Phase 2 extension points. Not implemented.

The ingestion service writes Job rows (source="agent" is reserved). A later
change can add an Approval table keyed by Job.id and mount new routers from
app.main without reshaping the Gmail sync path.

Both flows require a person to approve the outbound action. Implementations
must not submit an application or send a LinkedIn message on their own.
"""

from __future__ import annotations

from typing import Protocol


class ApprovalQueue(Protocol):
    def enqueue(self, clerk_id: str, kind: str, payload: dict) -> str:
        """Store a pending action and return its id. kind is 'apply' or 'referral'."""
        ...

    def approve(self, clerk_id: str, approval_id: str) -> None:
        """Mark an action approved. The worker that submits it is separate."""
        ...

    def reject(self, clerk_id: str, approval_id: str) -> None:
        """Drop a pending action without sending it."""
        ...


class ApplyAgent(Protocol):
    """Playwright apply flow. prepare() may open a browser and fill a form.

    It must stop before the final submit and enqueue that submit on ApprovalQueue.
    """

    def prepare(self, clerk_id: str, job_id: str) -> str:
        """Return an approval id for the filled-but-not-submitted application."""
        ...


class ReferralOutreach(Protocol):
    """LinkedIn referral messages.

    Implementations must enforce a low daily cap and enqueue every message for
    per-message approval. Drafting does not send.
    """

    def draft_message(self, clerk_id: str, job_id: str, contact: dict) -> str:
        """Return an approval id for one referral message."""
        ...
