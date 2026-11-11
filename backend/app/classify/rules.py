"""High-precision recruiting-email rules.

An OpenAI-compatible model fills gaps when these rules are unsure. The rules
are the source of truth for obvious mail so a sync still works with no LLM key.
"""

from __future__ import annotations

import re

from app.gmail.parse import ParsedEmail
from app.jobs.upsert import Extraction

_CONTEXT = re.compile(
    r"\b(appl(y|ied|ication|icant)|interview|role|position|candidate|recruiter|offer|assessment|hiring)\b",
    re.I,
)
_WEAK = re.compile(r"\b(job|career|hiring|recruiter|applicant|opportunity|opening)\b", re.I)

_OFFER = [
    r"offer of employment",
    r"pleased to offer",
    r"delighted to offer",
    r"happy to offer you",
    r"extend(?:ing)? (?:you )?an offer",
    r"your offer (?:letter|from)",
    r"offer letter",
    r"congratulations.{0,40}\boffer\b",
]
_REJECTED = [
    r"not (?:be )?moving forward",
    r"not (?:to )?move forward",
    r"move forward with other",
    r"other candidates",
    r"regret to inform",
    r"will not be proceeding",
    r"position has been filled",
    r"decided not to",
    r"unsuccessful",
    r"we (?:will|won't|will not) be (?:progressing|proceeding)",
]
_ASSESSMENT = [
    r"online assessment",
    r"coding (?:assessment|challenge|test)",
    r"\bhackerrank\b",
    r"\bcodesignal\b",
    r"\bcodility\b",
    r"take[- ]home",
    r"technical assessment",
    r"skills assessment",
]
_INTERVIEW = [
    r"\binterview\b",
    r"phone screen",
    r"\bonsite\b",
    r"on-site",
    r"schedule (?:a|your) (?:call|chat|interview|time)",
    r"\bcalendly\b",
    r"meet the team",
    r"availability for (?:a )?(?:call|chat|interview)",
]
_APPLIED = [
    r"thank(?:s| you) for (?:your )?(?:interest in |applying|your application|application)",
    r"thanks for applying",
    r"(?:we |we've |have )?received your application",
    r"application (?:has been |was )?received",
    r"application (?:has been |was )?submitted",
    r"your application (?:for|to|at)\b",
]

# Company tokens keep their own case so a loose "at the" does not become a company.
# Keyword prefixes are case-insensitive via (?i:...).
# Periods are not part of the token so "Stripe. We'll" does not swallow the next sentence.
_COMPANY = r"[A-Z][A-Za-z0-9&'’]+(?:\s+[A-Z][A-Za-z0-9&'’]+){0,3}"
_ROLE = r"[A-Za-z0-9][A-Za-z0-9 /+&#.'’-]{1,80}"

# Ordered from most specific. Named groups "company" and "role" are optional.
_FIELD_PATTERNS = [
    rf"(?i:interview invitation)\s*[:\-—–]\s*(?P<company>{_COMPANY})\s*/\s*(?P<role>{_ROLE})",
    rf"(?i:for the )(?P<role>{_ROLE}) (?i:role|position|opening) (?i:at )(?P<company>{_COMPANY})\b",
    rf"(?i:position of )(?P<role>{_ROLE}) (?i:at )(?P<company>{_COMPANY})\b",
    rf"(?i:application for )(?:(?i:the ))?(?P<role>{_ROLE}) (?i:at )(?P<company>{_COMPANY})\b",
    rf"(?i:interest in )(?:(?i:the ))?(?P<role>{_ROLE}) (?i:role|position) (?i:at )(?P<company>{_COMPANY})\b",
    rf"(?i:for the )(?P<role>{_ROLE}) (?i:role|position|opening)\b",
    rf"\b(?P<company>{_COMPANY}) (?i:invited you)\b",
    rf"(?i:applying to )(?P<company>{_COMPANY})\b",
    rf"(?i:application to )(?P<company>{_COMPANY})\b",
    rf"(?i:your )(?P<company>{_COMPANY}) (?i:application)\b",
    rf"(?i:offer from )(?P<company>{_COMPANY})\b",
    rf"(?i:\bat )(?P<company>{_COMPANY})\b",
]

_LOCATION = re.compile(r"\blocation\s*[:\-]\s*(?P<loc>[A-Za-z][A-Za-z .,]{1,40})", re.I)
_URL = re.compile(r"https?://[^\s<>\"')\]]+")
_JOB_HOSTS = (
    "greenhouse.io",
    "lever.co",
    "ashbyhq.com",
    "myworkdayjobs.com",
    "smartrecruiters.com",
    "icims.com",
    "linkedin.com/jobs",
    "workable.com",
    "jobvite.com",
    "bamboohr.com",
    "recruitee.com",
)
_GENERIC_SENDERS = (
    "greenhouse",
    "lever",
    "myworkday",
    "workday",
    "ashby",
    "smartrecruiters",
    "icims",
    "linkedin",
    "hackerrank",
    "codesignal",
    "codility",
    "no-reply",
    "noreply",
    "do-not-reply",
    "notifications",
    "mailer-daemon",
)
_ORG_TRAILING = re.compile(
    r"\b(careers|recruiting|talent|jobs|hr|team|hiring|university)\b$",
    re.I,
)


def _matches(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, re.I) for pattern in patterns)


def extract_status(text: str) -> str | None:
    """offer > rejected > assessment > interview > applied."""
    if _matches(_OFFER, text):
        return "offer"
    has_context = _CONTEXT.search(text) is not None
    if _matches(_REJECTED, text) or (re.search(r"\bunfortunately\b", text, re.I) and has_context):
        return "rejected"
    if _matches(_ASSESSMENT, text):
        return "assessment"
    if _matches(_INTERVIEW, text):
        return "interview"
    if _matches(_APPLIED, text):
        return "applied"
    return None


def _clean_org(value: str | None) -> str | None:
    if not value:
        return None
    text = re.split(r"[.!?]", value, maxsplit=1)[0]
    text = re.sub(r"\s+", " ", text).strip(" \t\r\n.,-–—|:;\"'")
    text = re.sub(r"^(the|your|our)\s+", "", text, flags=re.I)
    text = _ORG_TRAILING.sub("", text).strip(" \t.,-–—|")
    if not text or len(text) < 2 or len(text) > 80:
        return None
    if text.lower() in {"the", "your", "our", "team", "hi", "hello", "inc", "llc", "re", "fw", "fwd"}:
        return None
    return text


def _clean_role(value: str | None) -> str | None:
    if not value:
        return None
    text = re.sub(r"\s+", " ", value).strip(" \t\r\n.,-–—|:;\"'")
    text = re.sub(r"^(the|a|an)\s+", "", text, flags=re.I)
    text = re.sub(r"\b(role|position|opening|opportunity)$", "", text, flags=re.I).strip(" \t.,-")
    if not text or len(text) < 2 or len(text) > 120:
        return None
    if text.lower() in {"the", "your", "our", "this", "that", "role", "position"}:
        return None
    return text


def _sender_company(sender: str) -> str | None:
    match = re.match(r'\s*"?(?P<name>[^"<]+?)"?\s*<[^>]+>', sender or "")
    if not match:
        return None
    name = match.group("name").strip()
    lowered = name.lower()
    if any(lowered == generic or lowered.startswith(generic + " ") for generic in _GENERIC_SENDERS):
        return None
    if any(token in lowered for token in ("no-reply", "noreply", "do-not-reply", "notifications")):
        return None
    return _clean_org(name)


def extract_job_url(text: str) -> str | None:
    urls = [match.rstrip(".,)") for match in _URL.findall(text or "")]

    def score(url: str) -> int:
        lowered = url.lower()
        if any(host in lowered for host in _JOB_HOSTS):
            return 2
        if re.search(r"/jobs?/", lowered):
            return 1
        return 0

    ranked = [url for url in urls if score(url) > 0]
    if not ranked:
        return None
    ranked.sort(key=score, reverse=True)
    return ranked[0][:500]


def extract_location(text: str) -> str | None:
    match = _LOCATION.search(text or "")
    if match:
        location = re.sub(r"\s+", " ", match.group("loc")).strip(" ,.")
        if len(location) >= 2:
            return location[:80]
    if re.search(r"\bremote\b", text or "", re.I):
        return "Remote"
    return None


def extract_mode(text: str) -> str | None:
    if re.search(r"\bintern(ship)?\b", text or "", re.I):
        return "internship"
    if re.search(r"\bpart[- ]time\b", text or "", re.I):
        return "part-time"
    if re.search(r"\bfull[- ]time\b", text or "", re.I):
        return "full-time"
    return None


def _fill_fields(text: str) -> tuple[str | None, str | None]:
    company = None
    role = None
    for pattern in _FIELD_PATTERNS:
        match = re.search(pattern, text)
        if not match:
            continue
        groups = match.groupdict()
        if company is None and "company" in groups:
            company = _clean_org(groups.get("company"))
        if role is None and "role" in groups:
            role = _clean_role(groups.get("role"))
        if company and role:
            break
    return company, role


def classify_with_rules(email: ParsedEmail) -> Extraction:
    subject = re.sub(r"^(re|fw|fwd)\s*:\s*", "", (email.subject or "").strip(), flags=re.I)
    body = (email.body or "")[:8000]
    text = f"{subject}\n{body}"
    status = extract_status(text)
    company, position = _fill_fields(text)
    if company is None:
        company = _sender_company(email.sender)
    location = extract_location(text)
    mode = extract_mode(text)
    job_url = extract_job_url(text)

    if status is None:
        if _WEAK.search(text):
            return Extraction(
                is_application=False,
                company=company,
                position=position,
                location=location,
                mode=mode,
                job_url=job_url,
                confidence=0.35,
                needs_review=True,
                reason="weak hiring signal",
            )
        return Extraction(
            is_application=False,
            confidence=0.92,
            needs_review=False,
            reason="not an application",
        )

    filled = sum(1 for value in (company, position, status) if value)
    confidence = 0.5 + (0.15 * filled)
    return Extraction(
        is_application=True,
        company=company,
        position=position,
        status=status,
        location=location,
        mode=mode,
        job_url=job_url,
        confidence=confidence,
        needs_review=not (company and position),
        reason="rules",
    )
