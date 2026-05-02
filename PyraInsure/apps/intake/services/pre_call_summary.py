from __future__ import annotations

from typing import Any

from django.utils import timezone

from apps.customers.models import AgentNote, CustomerRecord, PreCallSummary
from apps.customers.services.customer_intelligence import (
    build_customer_detail_payload,
    score_label_for_value,
)
from apps.gap_scoring.models import GapFinding, TalkingPoint
from apps.intake.models import IntakeSubmission
from apps.referrals.models import ReferralOpportunity


def _latest_session(customer: CustomerRecord, intake_session_id: int | None = None) -> IntakeSubmission | None:
    if intake_session_id:
        return (
            IntakeSubmission.objects.filter(customer=customer, id=intake_session_id)
            .select_related("questionnaire_link", "agent")
            .first()
        )
    return (
        IntakeSubmission.objects.filter(customer=customer)
        .select_related("questionnaire_link", "agent")
        .order_by("-submitted_at", "-created_at")
        .first()
    )


def get_ordered_talking_points(customer_id: int, intake_session_id: int | None = None) -> list[TalkingPoint]:
    queryset = TalkingPoint.objects.filter(customer_id=customer_id, status="active")
    if intake_session_id:
        queryset = queryset.filter(intake_session_id=intake_session_id)
    else:
        queryset = queryset.order_by("-created_at")
    return list(queryset.order_by("-priority", "-created_at"))


def get_do_not_bring_up_notes(customer_id: int, intake_session_id: int | None = None) -> list[str]:
    queryset = AgentNote.objects.filter(customer_id=customer_id, note_type="do_not_bring_up")
    if intake_session_id:
        queryset = queryset.filter(intake_session_id=intake_session_id)
    return [note.note for note in queryset.order_by("-created_at") if note.note.strip()]


def _household_fact_summary(customer_detail_payload: dict[str, Any]) -> dict[str, Any]:
    metrics = customer_detail_payload.get("metrics", {})
    return {
        "household_size": metrics.get("household_size", 0),
        "spouse_present": metrics.get("spouse_present", False),
        "dependent_count": metrics.get("dependent_count", 0),
        "uncovered_household_count": metrics.get("uncovered_household_count", 0),
        "active_coverage_count": metrics.get("active_coverage_count", 0),
        "coverage_gap_count": metrics.get("coverage_gap_count", 0),
        "referral_opportunity_count": metrics.get("referral_opportunity_count", 0),
    }


def generate_avery_read(
    context: dict[str, Any],
    findings: list[GapFinding],
    talking_points: list[TalkingPoint],
    notes: list[str],
) -> str:
    customer_name = context.get("customer_name", "Customer")
    household_size = context.get("household_size", 0)
    opener = talking_points[0].title if talking_points else "the main coverage goal"
    top_finding = findings[0].title if findings else "the intake responses"
    referral_titles = [finding.title for finding in findings if finding.category != "health"][:2]

    statements = [
        f"Avery's read: {customer_name} has household size {household_size}.",
        f"Start with {opener.lower()} as the warm opener.",
        f"Top risk to address first: {top_finding.lower()}.",
    ]
    if referral_titles:
        statements.append(
            "Referral opportunities to introduce carefully if the customer is open: "
            + ", ".join(title.lower() for title in referral_titles)
            + "."
        )
    if notes:
        statements.append("Internal caution flags are on file; avoid excluded topics during the call.")
    return " ".join(statements)


def _score_delta(customer: CustomerRecord, current_gap_score: float, current_session_id: int | None) -> str | None:
    submissions = list(
        IntakeSubmission.objects.filter(customer=customer)
        .exclude(id=current_session_id)
        .order_by("-submitted_at", "-created_at")[:1]
    )
    if not submissions:
        return None
    previous_submission = submissions[0]
    previous_score = sum(
        finding.points
        for finding in GapFinding.objects.filter(submission=previous_submission)
    )
    previous_score = min(previous_score, 100)
    delta = int(current_gap_score - previous_score)
    if delta == 0:
        return "0 pts"
    sign = "+" if delta > 0 else "-"
    return f"{sign}{abs(delta)} pts"


def build_pre_call_summary(customer_id: int, intake_session_id: int | None = None) -> dict[str, Any]:
    customer = CustomerRecord.objects.select_related("agent").get(id=customer_id)
    session = _latest_session(customer, intake_session_id=intake_session_id)
    session_id = session.id if session else None

    customer_detail_payload = build_customer_detail_payload(customer)
    top_talking_points_payload = customer_detail_payload.get("top_talking_points", [])
    score = customer_detail_payload.get("score", {})
    gap_score = float(score.get("gap_score") or 0)
    findings_payload = customer_detail_payload.get("findings", [])

    talking_points = get_ordered_talking_points(customer_id, session_id)
    do_not_bring_up = get_do_not_bring_up_notes(customer_id, session_id)
    findings_qs = GapFinding.objects.filter(customer=customer)
    if session_id:
        findings_qs = findings_qs.filter(submission_id=session_id)
    findings = list(findings_qs.order_by("-points", "-created_at"))

    avery_read = generate_avery_read(
        context={
            "customer_name": customer.full_name,
            "household_size": customer_detail_payload.get("metrics", {}).get("household_size", 0),
        },
        findings=findings,
        talking_points=talking_points,
        notes=do_not_bring_up,
    )

    summary_instance, _created = PreCallSummary.objects.update_or_create(
        customer=customer,
        intake_session=session,
        defaults={
            "summary_text": avery_read,
            "avery_read": avery_read,
            "talking_point_order": [item["id"] for item in top_talking_points_payload],
            "do_not_bring_up": do_not_bring_up,
            "generated_at": timezone.now(),
        },
    )

    ordered_points = top_talking_points_payload
    if session_id:
        ordered_points = [
            item
            for item in top_talking_points_payload
            if any(
                finding.get("id") in [related.get("id") for related in item.get("related_findings", [])]
                for finding in findings_payload
            )
        ] or top_talking_points_payload

    referrals = list(
        ReferralOpportunity.objects.filter(customer=customer, submission_id=session_id).order_by("-updated_at")
    ) if session_id else list(
        ReferralOpportunity.objects.filter(customer=customer).order_by("-updated_at")[:5]
    )

    summary_payload = {
        "customer": customer_detail_payload["customer"],
        "summary": {
            "avery_read": avery_read,
            "gap_score": gap_score,
            "gap_score_label": score_label_for_value(gap_score),
            "gap_delta": _score_delta(customer, gap_score, session_id),
            "generated_at": summary_instance.generated_at.isoformat() if summary_instance.generated_at else None,
        },
        "talking_points": ordered_points,
        "do_not_bring_up": do_not_bring_up,
        "household_facts": _household_fact_summary(customer_detail_payload),
        "call_metadata": {
            "latest_submission_id": session_id,
            "latest_submission_at": session.submitted_at.isoformat() if session and session.submitted_at else None,
            "referral_opportunity_count": len(referrals),
        },
    }
    return summary_payload
