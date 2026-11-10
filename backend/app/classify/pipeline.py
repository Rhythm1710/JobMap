"""Rules first. The LLM only runs when the rules are incomplete or unsure."""

from __future__ import annotations

from app.classify.llm import LLMClassifier
from app.classify.rules import classify_with_rules
from app.gmail.parse import ParsedEmail
from app.jobs.upsert import Extraction


def merge_extractions(rules: Extraction, llm: Extraction) -> Extraction:
    """Keep rule fields that already hit. Use the model to fill gaps and ambiguous cases."""
    rules_sure = rules.confidence >= 0.75 and bool(rules.status)
    company = rules.company or llm.company
    position = rules.position or llm.position
    status = rules.status if rules.status and rules_sure else (llm.status or rules.status)
    location = rules.location or llm.location
    mode = rules.mode or llm.mode
    job_url = rules.job_url or llm.job_url
    is_application = bool(rules.is_application or llm.is_application or status)
    if not is_application:
        return Extraction(
            is_application=False,
            company=company,
            position=position,
            location=location,
            mode=mode,
            job_url=job_url,
            confidence=max(rules.confidence, llm.confidence),
            needs_review=False,
            reason="llm",
        )
    return Extraction(
        is_application=True,
        company=company,
        position=position,
        status=status,
        location=location,
        mode=mode,
        job_url=job_url,
        confidence=max(rules.confidence, llm.confidence, 0.7),
        needs_review=not (company and position and status),
        reason="llm" if not rules_sure else "rules+llm",
    )


def classify_email(email: ParsedEmail, llm: LLMClassifier | None) -> Extraction:
    rules = classify_with_rules(email)
    rules_complete = bool(
        rules.is_application and rules.company and rules.position and rules.status and rules.confidence >= 0.75
    )
    rules_negative = (not rules.is_application) and rules.confidence >= 0.8 and not rules.needs_review
    if rules_complete or rules_negative or llm is None or not llm.enabled:
        return rules
    model = llm.classify(email)
    if model is None:
        return rules
    return merge_extractions(rules, model)
