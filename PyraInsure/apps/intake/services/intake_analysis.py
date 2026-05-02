from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from apps.customers.services.activity import record_analysis_event
from apps.gap_scoring.models import GapFinding, RuleConfig, ScoringWeight, TalkingPoint, TalkingPointTemplate
from apps.intake.models import HouseholdMember, IntakeAnswer, IntakeSubmission
from apps.referrals.models import ReferralOpportunity


SEVERITY_WEIGHT = {"critical": 4, "high": 3, "medium": 2, "low": 1}
MISSING_COVERAGE_VALUES = {"", "none", "missing", "unknown", "no", "false", "n"}
LOW_LIABILITY_VALUES = {"unknown", "low", "state_minimum", "minimum"}
INSUFFICIENT_COVERAGE_VALUES = {"insufficient", "low", "minimal", "basic"}
DEFAULT_RULES: dict[str, dict[str, Any]] = {
    "health_gap": {"title": "Household members need coverage with no current health plan", "severity": "critical", "points": 30, "category": "health"},
    "aca_follow_up": {"title": "Marketplace / ACA follow-up requested", "severity": "medium", "points": 10, "category": "health"},
    "medicare_follow_up": {"title": "Medicare follow-up requested", "severity": "medium", "points": 10, "category": "health"},
    "provider_network_review": {"title": "Provider network review needed", "severity": "medium", "points": 10, "category": "health"},
    "prescription_risk": {"title": "Prescriptions need plan review", "severity": "high", "points": 15, "category": "health"},
    "vision_gap": {"title": "Family vision coverage opportunity", "severity": "medium", "points": 10, "category": "health"},
    "dental_gap": {"title": "Family dental coverage opportunity", "severity": "medium", "points": 10, "category": "health"},
    "life_gap": {"title": "Family life insurance coverage opportunity", "severity": "high", "points": 20, "category": "life"},
    "spouse_uncovered": {"title": "Spouse may need coverage", "severity": "high", "points": 20, "category": "health"},
    "homeowners_gap": {"title": "Homeowner without homeowners insurance", "severity": "high", "points": 20, "category": "home"},
    "rental_property": {"title": "Rental property ownership", "severity": "medium", "points": 10, "category": "home"},
    "umbrella_gap": {"title": "Assets over $250k without umbrella coverage", "severity": "high", "points": 20, "category": "umbrella"},
    "liability_without_umbrella": {"title": "Extra liability risk without umbrella coverage", "severity": "high", "points": 20, "category": "umbrella"},
    "auto_liability_review": {"title": "Auto liability limits uncertain/low", "severity": "medium", "points": 10, "category": "auto"},
    "auto_gap": {"title": "No auto insurance reported", "severity": "high", "points": 20, "category": "auto"},
    "teen_driver_risk": {"title": "Teen driver risk present", "severity": "medium", "points": 10, "category": "auto"},
}
DEFAULT_TALKING_POINT_TEMPLATES: dict[str, tuple[str, str, str, str]] = {
    "health_gap": (
        "Health coverage for household members",
        "health",
        "Some household members may need coverage.",
        "I saw there may be a coverage gap for someone in the household. Want to start there?",
    ),
    "aca_follow_up": (
        "Marketplace / ACA follow-up",
        "health",
        "Customer appears open to ACA/Marketplace help.",
        "You mentioned wanting help with health coverage. I can walk through Marketplace options with you.",
    ),
    "medicare_follow_up": (
        "Medicare follow-up",
        "health",
        "Customer appears open to Medicare help.",
        "You mentioned Medicare support. I can walk through Medicare options with you.",
    ),
    "provider_network_review": (
        "Provider network review",
        "health",
        "Customer wants to keep preferred providers.",
        "Let's make sure your preferred doctors and facilities stay in-network.",
    ),
    "vision_gap": (
        "Vision plan for the family",
        "health",
        "Family vision coverage may be missing.",
        "Would adding vision for the family make sense if the monthly cost is reasonable?",
    ),
    "dental_gap": (
        "Dental plan for the family",
        "health",
        "Family dental coverage may be missing.",
        "Do you want me to check dental options while we review health coverage?",
    ),
    "life_gap": (
        "Term life protection",
        "life",
        "Household has spouse/dependents and may need life coverage.",
        "Have you thought about your own coverage now that others depend on your income?",
    ),
    "homeowners_gap": (
        "Homeowners coverage review",
        "property",
        "Customer may own a home without homeowners coverage.",
        "I noticed you may own your home. Do you already have homeowners coverage in place?",
    ),
    "umbrella_gap": (
        "Umbrella liability coverage",
        "referral",
        "Assets or liability exposure may justify umbrella coverage.",
        "With your assets and liability exposure, umbrella coverage may be worth reviewing.",
    ),
    "liability_without_umbrella": (
        "Umbrella liability coverage",
        "referral",
        "Assets or liability exposure may justify umbrella coverage.",
        "With your assets and liability exposure, umbrella coverage may be worth reviewing.",
    ),
    "rental_property": (
        "Rental property coverage review",
        "referral",
        "Rental property ownership creates a coverage review opportunity.",
        "Do you have landlord or rental property coverage set up for that property?",
    ),
    "auto_liability_review": (
        "Auto liability limit review",
        "referral",
        "Auto liability limits may be low or unknown.",
        "It may be worth checking whether your auto liability limits are high enough.",
    ),
    "auto_gap": (
        "Auto coverage gap",
        "referral",
        "Customer reports no auto insurance.",
        "You may have an auto coverage gap. Want to review options?",
    ),
    "teen_driver_risk": (
        "Teen driver exposure",
        "referral",
        "A teen driver can increase liability exposure.",
        "Since there's a teen driver in the household, it may be worth reviewing liability protection.",
    ),
}


@dataclass(frozen=True)
class AnalysisContext:
    customer_id: int
    intake_session_id: int
    household_size: int
    dependents_count: int
    spouse_present: bool
    household_needs_coverage: bool
    prescriptions_present: bool
    marketplace_interest: bool
    current_medical_coverage: str
    dental_coverage: str
    vision_coverage: str
    life_insurance_coverage: str
    spouse_coverage: str
    homeowner: bool
    homeowners_insurance: str
    rental_property: bool
    auto_insurance: str
    auto_liability_limits: str
    umbrella_coverage: str
    assets_over_250k: bool
    referral_interest: bool
    tobacco_use: bool
    state: str
    preferred_contact_method: str
    main_concern: str
    quick_facts: list[str]
    raw_answers: dict[str, Any]


@dataclass(frozen=True)
class FindingDraft:
    finding_type: str
    category: str
    title: str
    severity: str
    points: int
    explanation: str
    source_keys: list[str]


@dataclass(frozen=True)
class TalkingPointDraft:
    finding_type: str
    title: str
    category: str
    hook: str
    suggested_script: str
    priority: int
    quick_facts: list[str]


@dataclass(frozen=True)
class ScoreResult:
    raw_score: int
    capped_score: int


@dataclass(frozen=True)
class AnalysisResult:
    intake_session: IntakeSubmission
    findings: list[GapFinding]
    talking_points: list[TalkingPoint]
    referrals: list[ReferralOpportunity]
    raw_gap_score: int
    capped_gap_score: int


def _configured_rule(rule_key: str) -> dict[str, Any] | None:
    defaults = DEFAULT_RULES.get(rule_key)
    if defaults is None:
        return None

    config = (
        RuleConfig.objects.filter(rule_key=rule_key)
        .order_by("-updated_at")
        .first()
    )
    if config and not config.enabled:
        return None
    scoring_weight = (
        ScoringWeight.objects.filter(weight_key=rule_key, enabled=True)
        .order_by("-updated_at")
        .first()
    )
    weighted_points = int(scoring_weight.value) if scoring_weight is not None else None

    if config:
        return {
            "finding_type": rule_key,
            "category": defaults["category"],
            "title": config.title or defaults["title"],
            "severity": config.severity or defaults["severity"],
            "points": weighted_points if weighted_points is not None else config.points,
        }
    return {
        "finding_type": rule_key,
        "category": defaults["category"],
        "title": defaults["title"],
        "severity": defaults["severity"],
        "points": weighted_points if weighted_points is not None else defaults["points"],
    }


def _append_finding(
    *,
    findings: list[FindingDraft],
    rule_key: str,
    explanation: str,
    source_keys: list[str],
) -> None:
    rule = _configured_rule(rule_key)
    if not rule:
        return
    findings.append(
        FindingDraft(
            finding_type=rule_key,
            category=str(rule["category"]),
            title=str(rule["title"]),
            severity=str(rule["severity"]),
            points=int(rule["points"]),
            explanation=explanation,
            source_keys=source_keys,
        )
    )


def _normalize_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().lower()


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    normalized = _normalize_text(value)
    return normalized in {"1", "true", "t", "yes", "y", "on"}


def _coverage_missing(value: Any) -> bool:
    normalized = _normalize_text(value)
    return normalized in MISSING_COVERAGE_VALUES


def _coverage_insufficient(value: Any) -> bool:
    normalized = _normalize_text(value)
    return normalized in MISSING_COVERAGE_VALUES or normalized in INSUFFICIENT_COVERAGE_VALUES


def _coverage_exists(value: Any) -> bool:
    return not _coverage_missing(value)


def _auto_limits_low_or_unknown(value: Any) -> bool:
    normalized = _normalize_text(value)
    return normalized in LOW_LIABILITY_VALUES


def _get_answer(answers: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in answers:
            return answers[key]
    return None


def _contains_health_help_text(main_concern: str) -> bool:
    text = main_concern.lower()
    return "health" in text or "marketplace" in text or "aca" in text or "insurance help" in text


def _build_quick_facts(
    *,
    household_size: int,
    dependents_count: int,
    spouse_present: bool,
    medical_missing: bool,
    vision_missing: bool,
    assets_over_250k: bool,
    umbrella_missing: bool,
    rental_property: bool,
    auto_limits_low_or_unknown: bool,
) -> list[str]:
    facts: list[str] = [
        f"Household size: {household_size}",
        f"Dependents: {dependents_count}",
        f"Spouse present: {'yes' if spouse_present else 'no'}",
    ]
    if medical_missing:
        facts.append("No current medical coverage reported")
    if vision_missing:
        facts.append("No current vision coverage reported")
    if assets_over_250k:
        facts.append("Assets over $250k indicated")
    if umbrella_missing:
        facts.append("No umbrella coverage reported")
    if rental_property:
        facts.append("Rental property ownership indicated")
    if auto_limits_low_or_unknown:
        facts.append("Auto liability limits unknown/low")
    return facts


def build_analysis_context(intake_session: IntakeSubmission) -> AnalysisContext:
    answers_qs = IntakeAnswer.objects.filter(submission=intake_session).order_by("id")
    answers: dict[str, Any] = {}
    for answer in answers_qs:
        value: Any
        if isinstance(answer.normalized_value, dict):
            value = answer.normalized_value.get("normalized_value")
        elif answer.normalized_value is not None:
            value = answer.normalized_value
        else:
            value = answer.answer_value
        answers[answer.question_key] = value

    members = list(HouseholdMember.objects.filter(submission=intake_session))
    household_size = len(members)
    dependents_count = sum(1 for member in members if member.role == "dependent")
    spouse_present = any(member.role == "spouse" for member in members)
    household_needs_coverage = any(
        bool(member.needs_health_coverage)
        if member.needs_health_coverage is not None
        else bool(member.needs_coverage)
        for member in members
    )
    prescriptions_present = any(
        bool(member.has_prescriptions)
        if member.has_prescriptions is not None
        else bool(member.takes_prescriptions)
        for member in members
    )
    tobacco_use = any(bool(member.tobacco_user) for member in members)

    current_medical_coverage = _normalize_text(_get_answer(answers, "current_health_coverage", "current_medical_coverage", "medical_coverage"))
    dental_coverage = _normalize_text(_get_answer(answers, "has_dental_coverage", "dental_coverage"))
    vision_coverage = _normalize_text(_get_answer(answers, "has_vision_coverage", "vision_coverage"))
    life_insurance_coverage = _normalize_text(_get_answer(answers, "has_life_insurance", "life_insurance_coverage"))
    spouse_coverage = _normalize_text(_get_answer(answers, "spouse_coverage", "spouse_health_coverage", "spouse_has_coverage"))
    homeowners_insurance = _normalize_text(_get_answer(answers, "has_home_insurance", "has_homeowners_insurance"))
    auto_insurance = _normalize_text(_get_answer(answers, "has_auto_insurance", "auto_insurance"))
    auto_liability_limits = _normalize_text(_get_answer(answers, "auto_liability_limit", "auto_liability_limits"))
    umbrella_coverage = _normalize_text(_get_answer(answers, "has_umbrella", "umbrella_coverage"))

    marketplace_interest = _as_bool(_get_answer(answers, "want_marketplace_help", "marketplace_interest", "wants_health_help"))
    medicare_interest = _as_bool(_get_answer(answers, "want_medicare_help", "medicare_interest"))
    provider_prefers_network = _as_bool(_get_answer(answers, "has_preferred_doctors", "preferred_doctors"))
    referral_interest = any(
        _as_bool(_get_answer(answers, key))
        for key in (
            "consent_referral_sharing",
            "wants_life_referral",
            "wants_auto_referral",
            "wants_home_referral",
            "wants_umbrella_referral",
        )
    )
    homeowner = _as_bool(_get_answer(answers, "owns_home", "homeowner"))
    rental_property = _as_bool(_get_answer(answers, "owns_rental_property", "rental_property"))
    assets_over_250k = _as_bool(_get_answer(answers, "assets_over_250k", "assets_over_threshold"))
    main_concern = str(_get_answer(answers, "main_concern") or "").strip()

    medical_missing = _coverage_missing(current_medical_coverage)
    umbrella_missing = _coverage_missing(umbrella_coverage)
    vision_missing = _coverage_missing(vision_coverage)
    auto_limits_low_or_unknown = _auto_limits_low_or_unknown(auto_liability_limits)

    quick_facts = _build_quick_facts(
        household_size=household_size,
        dependents_count=dependents_count,
        spouse_present=spouse_present,
        medical_missing=medical_missing,
        vision_missing=vision_missing,
        assets_over_250k=assets_over_250k,
        umbrella_missing=umbrella_missing,
        rental_property=rental_property,
        auto_limits_low_or_unknown=auto_limits_low_or_unknown,
    )

    return AnalysisContext(
        customer_id=intake_session.customer_id or 0,
        intake_session_id=intake_session.id,
        household_size=household_size,
        dependents_count=dependents_count,
        spouse_present=spouse_present,
        household_needs_coverage=household_needs_coverage,
        prescriptions_present=prescriptions_present,
        marketplace_interest=marketplace_interest,
        current_medical_coverage=current_medical_coverage,
        dental_coverage=dental_coverage,
        vision_coverage=vision_coverage,
        life_insurance_coverage=life_insurance_coverage,
        spouse_coverage=spouse_coverage,
        homeowner=homeowner,
        homeowners_insurance=homeowners_insurance,
        rental_property=rental_property,
        auto_insurance=auto_insurance,
        auto_liability_limits=auto_liability_limits,
        umbrella_coverage=umbrella_coverage,
        assets_over_250k=assets_over_250k,
        referral_interest=referral_interest,
        tobacco_use=tobacco_use,
        state=str(_get_answer(answers, "state") or ""),
        preferred_contact_method=str(_get_answer(answers, "preferred_contact_method") or ""),
        main_concern=main_concern,
        quick_facts=quick_facts,
        raw_answers=answers,
    )


def generate_findings(context: AnalysisContext) -> list[FindingDraft]:
    findings: list[FindingDraft] = []
    medical_missing = _coverage_missing(context.current_medical_coverage)
    medical_unknown_or_missing = context.current_medical_coverage in {"", "unknown", "none", "missing"}
    vision_missing = _coverage_missing(context.vision_coverage)
    dental_missing = _coverage_missing(context.dental_coverage)
    umbrella_missing = _coverage_missing(context.umbrella_coverage)
    life_missing_or_insufficient = _coverage_insufficient(context.life_insurance_coverage)
    spouse_coverage_missing = context.spouse_coverage in {"", "none", "unknown", "missing"}
    auto_limits_low_or_unknown = _auto_limits_low_or_unknown(context.auto_liability_limits)
    auto_insurance_exists = _coverage_exists(context.auto_insurance)
    asks_for_health_help = _contains_health_help_text(context.main_concern)

    # Future expansion point: add additional deterministic rules in this section.
    if context.household_needs_coverage or medical_missing:
        _append_finding(
            findings=findings,
            rule_key="health_gap",
            explanation="One or more household members appear to need health coverage.",
            source_keys=["current_health_coverage", "household_members"],
        )

    if context.marketplace_interest or asks_for_health_help:
        _append_finding(
            findings=findings,
            rule_key="aca_follow_up",
            explanation="Customer indicated interest in Marketplace/ACA or general health insurance help.",
            source_keys=["want_marketplace_help", "main_concern"],
        )

    if _as_bool(context.raw_answers.get("want_medicare_help")):
        _append_finding(
            findings=findings,
            rule_key="medicare_follow_up",
            explanation="Customer indicated interest in Medicare support.",
            source_keys=["want_medicare_help"],
        )

    if _as_bool(context.raw_answers.get("has_preferred_doctors")):
        _append_finding(
            findings=findings,
            rule_key="provider_network_review",
            explanation="Customer indicated preferred doctors/facilities should remain in-network.",
            source_keys=["has_preferred_doctors"],
        )

    if context.prescriptions_present and medical_unknown_or_missing:
        _append_finding(
            findings=findings,
            rule_key="prescription_risk",
            explanation="Prescription usage appears present while medical coverage is missing or unknown.",
            source_keys=["takes_prescriptions", "current_health_coverage"],
        )

    if context.dependents_count > 0 and vision_missing:
        _append_finding(
            findings=findings,
            rule_key="vision_gap",
            explanation="Dependents are present and vision coverage appears missing.",
            source_keys=["has_vision_coverage", "household_members"],
        )

    if context.dependents_count > 0 and dental_missing:
        _append_finding(
            findings=findings,
            rule_key="dental_gap",
            explanation="Dependents are present and dental coverage appears missing.",
            source_keys=["has_dental_coverage", "household_members"],
        )

    if (context.spouse_present or context.dependents_count > 0) and life_missing_or_insufficient:
        _append_finding(
            findings=findings,
            rule_key="life_gap",
            explanation="Household has spouse/dependents and life insurance appears missing or insufficient.",
            source_keys=["has_life_insurance", "household_members"],
        )

    if context.spouse_present and spouse_coverage_missing:
        _append_finding(
            findings=findings,
            rule_key="spouse_uncovered",
            explanation="Spouse is present and spouse coverage appears missing or unknown.",
            source_keys=["spouse_coverage", "household_members"],
        )

    if context.homeowner and _coverage_missing(context.homeowners_insurance):
        _append_finding(
            findings=findings,
            rule_key="homeowners_gap",
            explanation="Homeownership is indicated while homeowners coverage appears missing.",
            source_keys=["owns_home", "has_home_insurance"],
        )

    if context.rental_property:
        _append_finding(
            findings=findings,
            rule_key="rental_property",
            explanation="Rental property ownership creates a coverage review opportunity.",
            source_keys=["owns_rental_property"],
        )

    if context.assets_over_250k and umbrella_missing:
        _append_finding(
            findings=findings,
            rule_key="umbrella_gap",
            explanation="Assets appear above threshold while umbrella coverage is missing.",
            source_keys=["assets_over_250k", "has_umbrella"],
        )

    if (auto_limits_low_or_unknown or context.rental_property or context.homeowner) and umbrella_missing:
        _append_finding(
            findings=findings,
            rule_key="liability_without_umbrella",
            explanation="Liability exposure indicators appear present while umbrella coverage is missing.",
            source_keys=["auto_liability_limit", "owns_home", "owns_rental_property", "has_umbrella"],
        )

    if auto_insurance_exists and auto_limits_low_or_unknown:
        _append_finding(
            findings=findings,
            rule_key="auto_liability_review",
            explanation="Auto insurance exists but liability limits appear low or unknown.",
            source_keys=["has_auto_insurance", "auto_liability_limit"],
        )

    if _coverage_missing(context.auto_insurance):
        _append_finding(
            findings=findings,
            rule_key="auto_gap",
            explanation="Auto insurance appears missing.",
            source_keys=["has_auto_insurance"],
        )

    if _as_bool(context.raw_answers.get("teen_driver_in_household")):
        _append_finding(
            findings=findings,
            rule_key="teen_driver_risk",
            explanation="Teen driver indicated in household.",
            source_keys=["teen_driver_in_household"],
        )

    findings.sort(key=lambda item: (SEVERITY_WEIGHT[item.severity], item.points, item.title), reverse=True)
    return findings


def calculate_gap_score(findings: list[FindingDraft]) -> ScoreResult:
    raw_score = sum(item.points for item in findings)
    return ScoreResult(raw_score=raw_score, capped_score=min(raw_score, 100))


def generate_talking_points(context: AnalysisContext, findings: list[FindingDraft]) -> list[TalkingPointDraft]:
    templates = dict(DEFAULT_TALKING_POINT_TEMPLATES)
    for template in TalkingPointTemplate.objects.filter(enabled=True):
        templates[template.finding_type] = (
            template.title,
            template.category,
            template.hook,
            template.suggested_script,
        )

    drafts: list[TalkingPointDraft] = []
    seen_titles: set[str] = set()

    for finding in findings:
        template = templates.get(finding.finding_type)
        if not template:
            continue
        title, category, hook, script = template
        if title in seen_titles:
            continue
        seen_titles.add(title)
        priority = (SEVERITY_WEIGHT[finding.severity] * 100) + finding.points
        drafts.append(
            TalkingPointDraft(
                finding_type=finding.finding_type,
                title=title,
                category=category,
                hook=hook,
                suggested_script=script,
                priority=priority,
                quick_facts=context.quick_facts,
            )
        )

    drafts.sort(key=lambda item: item.priority, reverse=True)
    return drafts


def _build_referrals_from_findings(
    *,
    intake_session: IntakeSubmission,
    findings: list[GapFinding],
) -> list[ReferralOpportunity]:
    created: list[ReferralOpportunity] = []
    for finding in findings:
        if finding.category == "health":
            continue
        if finding.category not in {"life", "auto", "home", "umbrella"}:
            continue
        created.append(
            ReferralOpportunity.objects.create(
                submission=intake_session,
                customer=intake_session.customer,
                category=finding.category,
                severity=finding.severity,
                status="possible_opportunity",
                notes=finding.title,
            )
        )
    return created


def _update_customer_rollups(intake_session: IntakeSubmission, score: ScoreResult) -> None:
    customer = intake_session.customer
    if customer is None:
        return

    grouped_scores = (
        GapFinding.objects.filter(customer=customer, submission__isnull=False)
        .values("submission_id")
        .annotate(total_points=Sum("points"))
    )
    score_values = [min(int(item["total_points"] or 0), 100) for item in grouped_scores]
    average_score = score.capped_score if not score_values else sum(score_values) / len(score_values)

    customer.avg_gap_score = Decimal(str(average_score)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    customer.last_submission_at = intake_session.submitted_at or timezone.now()
    customer.save(update_fields=["avg_gap_score", "last_submission_at", "updated_at"])


def persist_analysis_results(
    intake_session: IntakeSubmission,
    findings: list[FindingDraft],
    talking_points: list[TalkingPointDraft],
    score: ScoreResult,
) -> AnalysisResult:
    customer = intake_session.customer
    if customer is None:
        return AnalysisResult(
            intake_session=intake_session,
            findings=[],
            talking_points=[],
            referrals=[],
            raw_gap_score=score.raw_score,
            capped_gap_score=score.capped_score,
        )

    with transaction.atomic():
        # Idempotency for generated data: replace generated rows for this intake session.
        GapFinding.objects.filter(submission=intake_session, is_generated=True).delete()
        TalkingPoint.objects.filter(intake_session=intake_session).delete()
        ReferralOpportunity.objects.filter(submission=intake_session).delete()
        customer.activities.filter(
            intake_session=intake_session,
            activity_type="intake_analyzed",
        ).delete()

        created_findings: list[GapFinding] = []
        for finding in findings:
            created = GapFinding.objects.create(
                submission=intake_session,
                customer=customer,
                finding_type=finding.finding_type,
                category=finding.category,
                severity=finding.severity,
                points=finding.points,
                title=finding.title,
                description=finding.explanation,
                explanation=finding.explanation,
                source_answer_ids=finding.source_keys,
                is_generated=True,
                status="open",
                assigned_to="hutchins" if finding.category == "health" else "partner_referral",
            )
            created_findings.append(created)
            record_analysis_event(
                customer_id=customer.id,
                intake_session_id=intake_session.id,
                activity_type="finding_created",
                title="Finding created",
                metadata={"finding_id": created.id, "finding_type": created.finding_type},
            )

        findings_by_type = {finding.finding_type: finding for finding in created_findings}
        created_talking_points: list[TalkingPoint] = []
        for talking_point in talking_points:
            related_finding = findings_by_type.get(talking_point.finding_type)
            related_ids = [related_finding.id] if related_finding else []
            created_talking_points.append(
                TalkingPoint.objects.create(
                    customer=customer,
                    intake_session=intake_session,
                    title=talking_point.title,
                    priority=talking_point.priority,
                    category=talking_point.category,
                    hook=talking_point.hook,
                    suggested_script=talking_point.suggested_script,
                    quick_facts=talking_point.quick_facts,
                    related_finding_ids=related_ids,
                    status="active",
                )
            )
            created_point = created_talking_points[-1]
            record_analysis_event(
                customer_id=customer.id,
                intake_session_id=intake_session.id,
                activity_type="talking_point_created",
                title="Talking point created",
                metadata={"talking_point_id": created_point.id},
            )

        created_referrals = _build_referrals_from_findings(intake_session=intake_session, findings=created_findings)

        record_analysis_event(
            customer_id=customer.id,
            intake_session_id=intake_session.id,
            activity_type="intake_analyzed",
            title="Intake analyzed",
            metadata={
                "finding_count": len(created_findings),
                "talking_point_count": len(created_talking_points),
                "score_raw": score.raw_score,
                "score_capped": score.capped_score,
            },
        )

        _update_customer_rollups(intake_session, score)

    return AnalysisResult(
        intake_session=intake_session,
        findings=created_findings,
        talking_points=created_talking_points,
        referrals=created_referrals,
        raw_gap_score=score.raw_score,
        capped_gap_score=score.capped_score,
    )


def analyze_intake_session(intake_session_id: int) -> AnalysisResult:
    intake_session = (
        IntakeSubmission.objects.select_related("customer")
        .filter(id=intake_session_id)
        .first()
    )
    if intake_session is None:
        raise IntakeSubmission.DoesNotExist(f"IntakeSubmission {intake_session_id} not found")

    context = build_analysis_context(intake_session)
    findings = generate_findings(context)
    score = calculate_gap_score(findings)
    talking_points = generate_talking_points(context, findings)
    return persist_analysis_results(intake_session, findings, talking_points, score)
