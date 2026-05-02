from __future__ import annotations

from decimal import Decimal
from typing import Any

from apps.customers.models import AgentNote, CoverageItem, CustomerActivity, CustomerRecord
from apps.gap_scoring.models import GapFinding, TalkingPoint
from apps.intake.models import HouseholdMember, IntakeAnswer, IntakeSubmission
from apps.referrals.models import ReferralOpportunity


SEVERITY_RANK = {"critical": 4, "high": 3, "medium": 2, "low": 1}


def _iso(value: Any) -> str | None:
    if value is None:
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _to_float(value: Decimal | float | int | None) -> float:
    if value is None:
        return 0.0
    return float(value)


def score_label_for_value(gap_score: float) -> str:
    if gap_score <= 19:
        return "Low gap"
    if gap_score <= 49:
        return "Moderate gap"
    if gap_score <= 79:
        return "High gap"
    return "Critical gap"


def _serialize_finding(finding: GapFinding) -> dict[str, Any]:
    return {
        "id": finding.id,
        "type": finding.finding_type or finding.category,
        "title": finding.title,
        "severity": finding.severity,
        "points": finding.points,
        "explanation": finding.explanation or finding.description,
        "status": finding.status,
        "created_at": _iso(finding.created_at),
    }


def _serialize_talking_point(
    talking_point: TalkingPoint,
    *,
    rank: int,
    related_finding_map: dict[int, GapFinding],
) -> dict[str, Any]:
    related_ids = [int(item) for item in (talking_point.related_finding_ids or []) if str(item).isdigit()]
    related_findings = [related_finding_map[item] for item in related_ids if item in related_finding_map]
    severity: str | None = None
    if related_findings:
        severity = sorted(related_findings, key=lambda finding: SEVERITY_RANK.get(finding.severity, 0), reverse=True)[0].severity

    return {
        "id": talking_point.id,
        "rank": rank,
        "title": talking_point.title,
        "category": talking_point.category or None,
        "priority": talking_point.priority,
        "severity": severity,
        "hook": talking_point.hook or None,
        "suggested_script": talking_point.suggested_script or None,
        "quick_facts": talking_point.quick_facts or [],
        "related_findings": [_serialize_finding(finding) for finding in related_findings],
    }


def _serialize_activity(activity: CustomerActivity) -> dict[str, Any]:
    return {
        "id": activity.id,
        "activity_type": activity.activity_type,
        "title": activity.title,
        "description": activity.description or None,
        "actor_name": activity.actor_name or None,
        "created_at": _iso(activity.created_at),
        "metadata": activity.metadata or {},
    }


def _serialize_household_member(member: HouseholdMember) -> dict[str, Any]:
    return {
        "id": member.id,
        "name": member.name or f"{member.first_name} {member.last_name}".strip(),
        "role": member.role,
        "dob": _iso(member.dob or member.date_of_birth),
        "age": member.age,
        "needs_health_coverage": member.needs_health_coverage if member.needs_health_coverage is not None else member.needs_coverage,
        "has_prescriptions": member.has_prescriptions if member.has_prescriptions is not None else member.takes_prescriptions,
        "notes": member.notes or None,
    }


def _serialize_coverage_item(item: CoverageItem | dict[str, Any]) -> dict[str, Any]:
    if isinstance(item, dict):
        return item
    return {
        "id": item.id,
        "coverage_type": item.coverage_type,
        "carrier": item.carrier or None,
        "plan_name": item.plan_name or None,
        "status": item.status.replace("_", " "),
        "gap_label": item.gap_label or None,
        "deductible": _to_float(item.deductible) if item.deductible is not None else None,
        "premium": _to_float(item.premium) if item.premium is not None else None,
        "notes": item.notes or None,
    }


def _normalized_answer_value(answer: IntakeAnswer) -> Any:
    if isinstance(answer.normalized_value, dict):
        return answer.normalized_value.get("display_value") or answer.normalized_value.get("normalized_value")
    if answer.normalized_value is not None:
        return answer.normalized_value
    return answer.answer_value


def _latest_submission_for_customer(customer: CustomerRecord) -> IntakeSubmission | None:
    return (
        customer.submissions.order_by("-submitted_at", "-created_at")
        .select_related("questionnaire_link")
        .first()
    )


def _finding_stats(findings: list[GapFinding]) -> tuple[int, int, int]:
    health_count = sum(1 for finding in findings if finding.category == "health")
    referral_count = sum(1 for finding in findings if finding.category != "health")
    return health_count, referral_count, len(findings)


def _top_finding(findings: list[GapFinding]) -> GapFinding | None:
    if not findings:
        return None
    return sorted(
        findings,
        key=lambda finding: (
            SEVERITY_RANK.get(finding.severity, 0),
            finding.points,
            finding.created_at,
        ),
        reverse=True,
    )[0]


def _session_gap_score(findings: list[GapFinding]) -> float:
    return float(min(sum(finding.points for finding in findings), 100))


def _build_customer_list_row(customer: CustomerRecord) -> dict[str, Any]:
    latest_submission = _latest_submission_for_customer(customer)
    latest_session_id = latest_submission.id if latest_submission else None
    latest_findings = list(
        GapFinding.objects.filter(submission=latest_submission).order_by("-created_at")
    ) if latest_submission else []

    health_gap_count, referral_gap_count, finding_count = _finding_stats(latest_findings)
    top_finding = _top_finding(latest_findings)
    score = _session_gap_score(latest_findings) if latest_findings else _to_float(customer.avg_gap_score)

    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "email": customer.email or None,
        "phone": customer.phone or None,
        "state": customer.state or None,
        "assigned_agent_name": customer.assigned_agent_name if customer.agent_id else None,
        "client_since": _iso(customer.client_since),
        "last_submission_at": _iso(customer.last_submission_at),
        "latest_intake_session_id": latest_session_id,
        "gap_score": score,
        "health_gap_count": health_gap_count,
        "referral_gap_count": referral_gap_count,
        "finding_count": finding_count,
        "top_finding_title": top_finding.title if top_finding else None,
        "status": customer.status,
        "created_at": _iso(customer.created_at),
    }


def _apply_customer_list_filters(rows: list[dict[str, Any]], params: dict[str, str]) -> list[dict[str, Any]]:
    search = params.get("search", "").strip().lower()
    if search:
        rows = [
            row
            for row in rows
            if search in (row["full_name"] or "").lower()
            or search in (row["email"] or "").lower()
            or search in (row["phone"] or "").lower()
        ]

    status = params.get("status", "").strip().lower()
    if status:
        rows = [row for row in rows if (row["status"] or "").lower() == status]

    state = params.get("state", "").strip().lower()
    if state:
        rows = [row for row in rows if (row["state"] or "").lower() == state]

    min_gap_score = params.get("min_gap_score")
    if min_gap_score:
        try:
            min_score = float(min_gap_score)
            rows = [row for row in rows if float(row["gap_score"] or 0) >= min_score]
        except ValueError:
            pass

    has_health_gaps = params.get("has_health_gaps", "").strip().lower()
    if has_health_gaps in {"1", "true", "yes"}:
        rows = [row for row in rows if row["health_gap_count"] > 0]

    has_referral_gaps = params.get("has_referral_gaps", "").strip().lower()
    if has_referral_gaps in {"1", "true", "yes"}:
        rows = [row for row in rows if row["referral_gap_count"] > 0]

    return rows


def _sort_customer_rows(rows: list[dict[str, Any]], params: dict[str, str]) -> list[dict[str, Any]]:
    sort_field = params.get("sort", "").strip().lower()
    direction = params.get("direction", "desc").strip().lower()
    reverse = direction != "asc"

    if sort_field == "gap_score":
        return sorted(rows, key=lambda row: float(row["gap_score"] or 0), reverse=reverse)
    if sort_field == "created_at":
        return sorted(rows, key=lambda row: row["created_at"] or "", reverse=reverse)
    if sort_field == "last_submission":
        return sorted(
            rows,
            key=lambda row: ((row["last_submission_at"] is None), row["last_submission_at"] or "", row["created_at"] or ""),
            reverse=reverse,
        )

    return sorted(
        rows,
        key=lambda row: (
            row["last_submission_at"] is None,
            row["last_submission_at"] or "",
            row["created_at"] or "",
        ),
        reverse=True,
    )


def build_customer_list_payload(
    *,
    base_queryset,
    params: dict[str, str],
) -> dict[str, Any]:
    rows = [_build_customer_list_row(customer) for customer in base_queryset]
    filtered_rows = _apply_customer_list_filters(rows, params)
    ordered_rows = _sort_customer_rows(filtered_rows, params)

    total = len(ordered_rows)
    try:
        offset = int(params.get("offset", "0") or 0)
    except ValueError:
        offset = 0
    try:
        limit = int(params.get("limit", "50") or 50)
    except ValueError:
        limit = 50
    offset = max(0, offset)
    limit = max(1, min(limit, 500))
    paged = ordered_rows[offset : offset + limit]

    return {
        "count": total,
        "limit": limit,
        "offset": offset,
        "results": paged,
    }


def _generated_coverage_items_from_findings(
    *,
    findings: list[GapFinding],
    existing_items: list[CoverageItem],
) -> list[dict[str, Any]]:
    existing_types = {item.coverage_type for item in existing_items}
    generated: list[dict[str, Any]] = []

    mapping = {
        "health_gap": ("medical", "Medical coverage gap inferred from findings."),
        "vision_gap": ("vision", "Vision coverage gap inferred from findings."),
        "dental_gap": ("dental", "Dental coverage gap inferred from findings."),
        "life_gap": ("life", "Life coverage gap inferred from findings."),
        "homeowners_gap": ("homeowners", "Homeowners coverage gap inferred from findings."),
        "umbrella_gap": ("umbrella", "Umbrella coverage gap inferred from findings."),
        "liability_without_umbrella": ("umbrella", "Liability exposure without umbrella inferred from findings."),
    }
    for finding in findings:
        mapped = mapping.get(finding.finding_type)
        if not mapped:
            continue
        coverage_type, notes = mapped
        if coverage_type in existing_types:
            continue
        if any(item["coverage_type"] == coverage_type for item in generated):
            continue
        generated.append(
            {
                "id": None,
                "coverage_type": coverage_type,
                "carrier": None,
                "plan_name": None,
                "status": "gap",
                "gap_label": finding.title,
                "deductible": None,
                "premium": None,
                "notes": notes,
            }
        )
    return generated


def _customer_profile_payload(customer: CustomerRecord) -> dict[str, Any]:
    return {
        "id": customer.id,
        "full_name": customer.full_name,
        "first_name": customer.first_name,
        "last_name": customer.last_name,
        "email": customer.email or None,
        "phone": customer.phone or None,
        "state": customer.state or None,
        "preferred_contact_method": customer.preferred_contact_method or None,
        "assigned_agent_name": customer.assigned_agent_name,
        "client_since": _iso(customer.client_since),
        "last_submission_at": _iso(customer.last_submission_at),
        "status": customer.status,
        "created_at": _iso(customer.created_at),
    }


def build_customer_detail_payload(customer: CustomerRecord) -> dict[str, Any]:
    latest_submission = _latest_submission_for_customer(customer)
    latest_findings = list(
        GapFinding.objects.filter(submission=latest_submission).order_by("-points", "-created_at")
    ) if latest_submission else []
    latest_referrals = list(
        ReferralOpportunity.objects.filter(submission=latest_submission).order_by("-updated_at")
    ) if latest_submission else []
    household_members = list(
        HouseholdMember.objects.filter(submission=latest_submission).order_by("created_at")
    ) if latest_submission else list(
        HouseholdMember.objects.filter(customer=customer).order_by("-created_at")
    )

    health_gap_count, referral_gap_count, finding_count = _finding_stats(latest_findings)
    gap_score = _session_gap_score(latest_findings) if latest_findings else _to_float(customer.avg_gap_score)
    coverage_items = list(CoverageItem.objects.filter(customer=customer).order_by("coverage_type", "-created_at"))
    generated_coverage = _generated_coverage_items_from_findings(findings=latest_findings, existing_items=coverage_items)

    talking_points_qs = TalkingPoint.objects.filter(customer=customer)
    if latest_submission:
        talking_points_qs = talking_points_qs.filter(intake_session=latest_submission)
    talking_points = list(talking_points_qs.order_by("-priority", "-created_at")[:3])
    related_finding_ids = {
        int(item)
        for talking_point in talking_points
        for item in (talking_point.related_finding_ids or [])
        if str(item).isdigit()
    }
    related_finding_map = {finding.id: finding for finding in GapFinding.objects.filter(id__in=related_finding_ids)}
    serialized_talking_points = [
        _serialize_talking_point(talking_point, rank=index + 1, related_finding_map=related_finding_map)
        for index, talking_point in enumerate(talking_points)
    ]

    recent_activity = [
        _serialize_activity(activity)
        for activity in customer.activities.order_by("-created_at")[:20]
    ]
    latest_notes = list(
        customer.agent_notes.order_by("-created_at")[:10]
    )

    household_size = len(household_members)
    spouse_present = any(member.role == "spouse" for member in household_members)
    dependent_count = sum(1 for member in household_members if member.role == "dependent")
    uncovered_household_count = sum(
        1
        for member in household_members
        if (member.needs_health_coverage if member.needs_health_coverage is not None else member.needs_coverage)
    )
    active_coverage_count = sum(1 for item in coverage_items if item.status == "active")
    coverage_gap_count = sum(1 for item in coverage_items if item.status == "gap") + len(generated_coverage)
    referral_opportunity_count = sum(1 for item in coverage_items if item.status == "referral_opportunity") + len(latest_referrals)

    return {
        "customer": _customer_profile_payload(customer),
        "household": [_serialize_household_member(member) for member in household_members],
        "coverage_items": [_serialize_coverage_item(item) for item in coverage_items] + generated_coverage,
        "score": {
            "gap_score": gap_score,
            "label": score_label_for_value(gap_score),
            "health_gap_count": health_gap_count,
            "referral_gap_count": referral_gap_count,
            "finding_count": finding_count,
        },
        "metrics": {
            "household_size": household_size,
            "spouse_present": spouse_present,
            "dependent_count": dependent_count,
            "uncovered_household_count": uncovered_household_count,
            "active_coverage_count": active_coverage_count,
            "coverage_gap_count": coverage_gap_count,
            "referral_opportunity_count": referral_opportunity_count,
        },
        "top_talking_points": serialized_talking_points,
        "recent_activity": recent_activity,
        "findings": [_serialize_finding(finding) for finding in latest_findings[:25]],
        "latest_session": {
            "id": latest_submission.id,
            "status": latest_submission.status,
            "source": latest_submission.source,
            "submitted_at": _iso(latest_submission.submitted_at),
            "created_at": _iso(latest_submission.created_at),
            "public_token": latest_submission.public_token,
        } if latest_submission else None,
        "notes": [
            {
                "id": note.id,
                "note_type": note.note_type,
                "note": note.note,
                "created_by": note.created_by.get_username() if note.created_by else None,
                "created_at": _iso(note.created_at),
            }
            for note in latest_notes
        ],
    }


def build_submission_analysis_payload(submission: IntakeSubmission) -> dict[str, Any]:
    customer = submission.customer
    findings = list(GapFinding.objects.filter(submission=submission).order_by("-points", "-created_at"))
    talking_points = list(TalkingPoint.objects.filter(intake_session=submission).order_by("-priority", "-created_at"))
    referrals = list(ReferralOpportunity.objects.filter(submission=submission).order_by("-updated_at"))
    answers = list(IntakeAnswer.objects.filter(submission=submission).order_by("id"))
    household = list(HouseholdMember.objects.filter(submission=submission).order_by("created_at"))
    do_not_bring_up_notes = list(
        AgentNote.objects.filter(
            customer=submission.customer,
            intake_session=submission,
            note_type="do_not_bring_up",
        ).order_by("-created_at")
    ) if submission.customer_id else []

    related_finding_ids = {
        int(item)
        for talking_point in talking_points
        for item in (talking_point.related_finding_ids or [])
        if str(item).isdigit()
    }
    related_finding_map = {finding.id: finding for finding in GapFinding.objects.filter(id__in=related_finding_ids)}
    serialized_talking_points = [
        _serialize_talking_point(talking_point, rank=index + 1, related_finding_map=related_finding_map)
        for index, talking_point in enumerate(talking_points)
    ]

    raw_score = int(sum(finding.points for finding in findings))
    capped_score = min(raw_score, 100)

    return {
        "customer": _customer_profile_payload(customer) if customer else None,
        "session": {
            "id": submission.id,
            "status": submission.status,
            "submitted_at": _iso(submission.submitted_at),
            "created_at": _iso(submission.created_at),
            "source": submission.source,
            "public_token": submission.public_token,
        },
        "key_talking_points": serialized_talking_points[:5],
        "household": [_serialize_household_member(member) for member in household],
        "findings": [_serialize_finding(finding) for finding in findings],
        "referral_opportunities": [
            {
                "id": referral.id,
                "category": referral.category,
                "severity": referral.severity,
                "status": referral.status,
                "notes": referral.notes or None,
                "created_at": _iso(referral.created_at),
            }
            for referral in referrals
        ],
        "score": {
            "raw_gap_score": raw_score,
            "gap_score": capped_score,
            "label": score_label_for_value(capped_score),
            "health_gap_count": sum(1 for finding in findings if finding.category == "health"),
            "referral_gap_count": sum(1 for finding in findings if finding.category != "health"),
            "finding_count": len(findings),
        },
        "answers": [
            {
                "id": answer.id,
                "question_key": answer.question_key,
                "question_text": answer.question_text,
                "answer_value": _normalized_answer_value(answer),
                "module": answer.module or None,
                "supports": answer.supports.split(",") if answer.supports else [],
                "created_at": _iso(answer.created_at),
            }
            for answer in answers
        ],
        "do_not_bring_up_notes": [note.note for note in do_not_bring_up_notes],
    }
