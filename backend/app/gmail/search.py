from datetime import datetime, timedelta, timezone

# Broad recruiting search. The classifier, not this query, decides what becomes a job.
# It is intentionally wider than "internship" and it is not limited to unread mail.
GMAIL_SEARCH = (
    "("
    "subject:(application OR applied OR applying OR interview OR assessment OR offer "
    'OR rejection OR rejected OR unfortunately OR recruiter OR "next steps" '
    'OR "coding challenge" OR hackerrank OR codesignal OR codility OR "thank you for") '
    'OR "thank you for applying" OR "application received" OR "we received your application" '
    'OR "move forward" OR "phone screen" OR onsite OR "online assessment" OR "offer letter"'
    ")"
)


def build_search_query(lookback_days: int, before: datetime | None, now: datetime | None = None) -> str:
    current = now or datetime.now(timezone.utc).replace(tzinfo=None)
    after = int((current - timedelta(days=lookback_days)).timestamp())
    query = f"{GMAIL_SEARCH} after:{after}"
    if before is not None:
        query += f" before:{int(before.timestamp())}"
    return query
