import json

from app.classify.llm import parse_llm_payload
from app.classify.pipeline import classify_email, merge_extractions
from app.classify.rules import classify_with_rules
from app.gmail.parse import parse_gmail_message
from app.gmail.search import build_search_query
from app.jobs.normalize import normalize_key, normalize_role
from app.jobs.upsert import Extraction
from datetime import datetime

from tests.fixtures import gmail_payload, parsed


def test_application_confirmation_extracts_company_role_and_status():
    result = classify_with_rules(
        parsed(
            "Thank you for applying to Stripe",
            "Hi Ada,\n\nWe received your application for the Backend Engineer role at Stripe. "
            "We'll review it and be in touch.\n",
            sender="Stripe <no-reply@us.greenhouse-mail.io>",
        )
    )
    assert result.is_application is True
    assert result.status == "applied"
    assert result.company == "Stripe"
    assert result.position == "Backend Engineer"
    assert result.confidence >= 0.75


def test_rejection_wins_over_thank_you_language():
    result = classify_with_rules(
        parsed(
            "Update on your Notion application",
            "Thank you for your interest in the Product Designer position at Notion. "
            "Unfortunately, we have decided not to move forward.",
            sender="Notion Careers <no-reply@hire.lever.co>",
        )
    )
    assert result.status == "rejected"
    assert result.company == "Notion"
    assert result.position == "Product Designer"


def test_interview_subject_splits_company_and_role():
    result = classify_with_rules(
        parsed(
            "Interview invitation — Acme / Senior Software Engineer",
            "We'd like to schedule a phone screen. Pick a time: https://calendly.com/acme/screen",
            sender="Acme Recruiting <talent@acme.com>",
        )
    )
    assert result.status == "interview"
    assert result.company == "Acme"
    assert result.position == "Senior Software Engineer"
    assert result.job_url is None  # calendly is not a job posting


def test_online_assessment_beats_a_passing_interview_mention():
    result = classify_with_rules(
        parsed(
            "Your HackerRank assessment for Stripe",
            "Please complete this online assessment before your interview for the "
            "Software Engineer Intern role at Stripe.\nhttps://www.hackerrank.com/tests/abc123",
            sender="HackerRank <noreply@hackerrank.com>",
        )
    )
    assert result.status == "assessment"
    assert result.company == "Stripe"
    assert result.position == "Software Engineer Intern"
    assert result.mode == "internship"
    assert result.job_url is None


def test_codesignal_invite_uses_the_inviting_company():
    result = classify_with_rules(
        parsed(
            "CodeSignal assessment",
            "Datadog invited you to a CodeSignal coding assessment for the Frontend Engineer role.",
            sender="CodeSignal <noreply@codesignal.com>",
        )
    )
    assert result.status == "assessment"
    assert result.company == "Datadog"
    assert result.position == "Frontend Engineer"


def test_offer_extracts_role_and_company():
    result = classify_with_rules(
        parsed(
            "Your offer from Figma",
            "We're delighted to offer you the position of Product Engineer at Figma. "
            "The offer letter is attached.",
            sender="Figma <people@figma.com>",
        )
    )
    assert result.status == "offer"
    assert result.company == "Figma"
    assert result.position == "Product Engineer"


def test_workday_confirmation_keeps_posting_url_and_location():
    result = classify_with_rules(
        parsed(
            "Thank you for applying",
            "Your application for Data Scientist at Spotify has been received.\n"
            "Location: New York\n"
            "https://spotify.wd5.myworkdayjobs.com/Spotify/job/NYC/Data-Scientist_123\n",
            sender="Spotify <no-reply@myworkday.com>",
        )
    )
    assert result.status == "applied"
    assert result.company == "Spotify"
    assert result.position == "Data Scientist"
    assert result.location == "New York"
    assert result.job_url is not None
    assert "myworkdayjobs.com" in result.job_url


def test_newsletter_is_not_an_application():
    result = classify_with_rules(
        parsed(
            "This week in tech",
            "Top stories: a startup raised a series B. No action needed.",
            sender="TLDR <news@tldr.tech>",
        )
    )
    assert result.is_application is False
    assert result.needs_review is False
    assert result.confidence >= 0.8


def test_weak_hiring_email_is_flagged_for_review():
    result = classify_with_rules(
        parsed(
            "Quick question about your background",
            "I came across your profile and we are hiring.",
            sender="Sam Recruiter <sam@example.com>",
        )
    )
    assert result.is_application is False
    assert result.needs_review is True


def test_rules_skip_the_llm_when_they_are_confident():
    class Boom:
        enabled = True

        def classify(self, email):
            raise AssertionError("llm should not run")

    email = parsed(
        "Thank you for applying to Stripe",
        "We received your application for the Backend Engineer role at Stripe.",
        sender="Stripe <no-reply@greenhouse-mail.io>",
    )
    result = classify_email(email, Boom())
    assert result.company == "Stripe"
    assert result.status == "applied"


def test_llm_fills_an_ambiguous_email_and_does_not_override_rule_status():
    rules = Extraction(
        is_application=True,
        company=None,
        position=None,
        status="rejected",
        confidence=0.8,
        reason="rules",
    )
    model = Extraction(
        is_application=True,
        company="Plaid",
        position="Support Engineer",
        status="applied",
        confidence=0.6,
        reason="llm",
    )
    merged = merge_extractions(rules, model)
    assert merged.company == "Plaid"
    assert merged.position == "Support Engineer"
    assert merged.status == "rejected"


def test_llm_payload_rejects_unknown_status_as_junk():
    payload = parse_llm_payload(
        json.loads(
            '{"is_application": true, "company": "Linear", "position": "Designer", '
            '"status": "hired", "mode": "full-time", "confidence": 0.4}'
        )
    )
    assert payload is None


def test_parse_gmail_message_reads_plain_and_html():
    when = datetime(2026, 3, 1, 8, 30, 0)
    plain = parse_gmail_message(
        gmail_payload("m", "t", "Hello", "Thank you for applying to Stripe", "Stripe <a@b.c>", when)
    )
    assert plain.subject == "Hello"
    assert "Stripe" in plain.body
    assert plain.received_at == when
    html = parse_gmail_message(
        gmail_payload(
            "m2",
            "t2",
            "Hi",
            "<html><body><p>Backend Engineer</p><script>nope</script></body></html>",
            "A <a@b.c>",
            when,
            html=True,
        )
    )
    assert "Backend Engineer" in html.body
    assert "nope" not in html.body


def test_search_query_is_not_limited_to_unread_or_internship():
    query = build_search_query(30, datetime(2026, 2, 1), now=datetime(2026, 3, 1))
    assert "is:unread" not in query
    assert "internship" not in query.split()  # the keyword list is broader than internship
    assert "after:" in query
    assert "before:" in query
    assert "interview" in query
    assert "assessment" in query


def test_normalize_strips_company_suffixes_and_role_noise():
    assert normalize_key("Stripe, Inc.") == "stripe"
    assert normalize_key("Acme LLC") == "acme"
    assert normalize_role("Backend Engineer role") == "backend engineer"
    assert normalize_role("Software Engineer Intern") == "software engineer intern"
