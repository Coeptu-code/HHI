from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from django.utils import timezone

from apps.gap_scoring.models import GapFinding
from apps.intake.models import IntakeSubmission
from apps.referrals.models import ReferralOpportunity


MODULE_ORDER = ("health", "life", "auto", "home", "umbrella")
MODULE_LABELS = {
    "health": "Health",
    "life": "Life",
    "auto": "Auto",
    "home": "Home",
    "umbrella": "Umbrella",
}

SEVERITY_POINTS = {
    "critical": 30,
    "high": 20,
    "medium": 10,
    "low": 5,
}


@dataclass(frozen=True)
class ScoringResult:
    total_points: int
    coverage_score: int
    findings: list[GapFinding]
    referrals: list[ReferralOpportunity]


@dataclass(frozen=True)
class ModuleScorecard:
    category: str
    label: str
    score: int
    gap_points: int
    items_to_review: list[str]


@dataclass(frozen=True)
class CoveraGapScorecard:
    overall_score: int
    gap_risk_score: int
    modules: list[ModuleScorecard]


def _as_bool(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, bool):
        return value
    s = str(value).strip().lower()
    return s in {"1", "true", "t", "yes", "y", "on"}


def _clamp_score(value: int) -> int:
    return max(0, min(100, value))


def _client_safe_review_item(finding: GapFinding) -> str:
    title = finding.title.lower()
    description = finding.description.lower()

    if finding.category == "health":
        if "need coverage" in title or "no current health plan" in description:
            return "You indicated that someone in your household may need health coverage."
        if "prescriptions without health coverage" in title:
            return "You indicated prescription medications may need to be reviewed along with current coverage needs."
        if "medication and formulary review" in title:
            return "You indicated prescription medications may need to be reviewed for plan fit."
        if "marketplace" in title:
            return "You indicated you would like help reviewing Marketplace coverage options."
        if "medicare" in title:
            return "You indicated you would like help reviewing Medicare coverage options."
        if "preferred doctors" in title:
            return "You indicated a preferred doctor or facility may need to be checked for network fit."
        if "other coverage eligibility" in title:
            return "You indicated someone in your household may have access to other coverage that should be reviewed."
        if "tobacco use" in title:
            return "You indicated tobacco use in the household, which may affect future health plan review."
    elif finding.category == "life":
        if "dependents" in title or "income reliance" in title:
            return "You indicated someone may depend on your income or care."
        if "debt exposure" in title:
            return "You indicated a mortgage or major debt may need protection planning."
        if "requested life coverage review" in title:
            return "You indicated you would like to review life coverage."
    elif finding.category == "auto":
        if "no auto insurance" in title:
            return "You indicated vehicle coverage may need review."
        if "liability limits" in title:
            return "You indicated auto liability limits may need review."
        if "requested auto coverage review" in title:
            return "You indicated you would like to review vehicle coverage."
    elif finding.category == "home":
        if "homeowner without homeowners insurance" in title:
            return "You indicated homeowners coverage may need review."
        if "rental property ownership" in title:
            return "You indicated rental property ownership may need additional review."
        if "requested home coverage review" in title:
            return "You indicated you would like to review property coverage."
    elif finding.category == "umbrella":
        if "assets over $250k" in title:
            return "You indicated assets may need added liability protection."
        if "extra liability risk" in title:
            return "You indicated extra liability risks may need review."
        if "requested umbrella coverage review" in title:
            return "You indicated you would like to review extra liability protection."

    fallback = (finding.description or finding.title).strip().replace("Client reports", "You indicated")
    fallback = fallback.replace("Client requested", "You indicated")
    fallback = fallback.replace("client reports", "you indicated")
    fallback = fallback.replace("client requested", "you indicated")
    fallback = fallback.replace("Consider referral opportunity.", "")
    fallback = fallback.replace("Consider referral for property/umbrella review.", "")
    fallback = fallback.replace("Consider referral to a licensed partner agent.", "")
    fallback = fallback.replace("licensed partner agent", "licensed insurance professional")
    fallback = " ".join(fallback.split())
    return fallback.rstrip(".") + "."


def build_coveragap_score(submission: IntakeSubmission) -> CoveraGapScorecard:
    findings = list(submission.gap_findings.order_by("-points", "created_at"))
    selected_modules = submission.questionnaire_link.selected_modules()

    total_points = sum(finding.points for finding in findings)
    overall_score = _clamp_score(max(0, 100 - total_points))
    categories = [
        category
        for category in MODULE_ORDER
        if category in selected_modules or any(finding.category == category for finding in findings)
    ]

    modules: list[ModuleScorecard] = []
    for category in categories:
        category_findings = [finding for finding in findings if finding.category == category]
        category_points = sum(finding.points for finding in category_findings)
        items_to_review: list[str] = []
        for finding in category_findings:
            item = _client_safe_review_item(finding)
            if item not in items_to_review:
                items_to_review.append(item)

        modules.append(
            ModuleScorecard(
                category=category,
                label=MODULE_LABELS[category],
                score=_clamp_score(max(0, 100 - category_points)),
                gap_points=category_points,
                items_to_review=items_to_review,
            )
        )

    return CoveraGapScorecard(
        overall_score=overall_score,
        gap_risk_score=total_points,
        modules=modules,
    )


def score_and_persist(submission: IntakeSubmission, answers: dict[str, Any]) -> ScoringResult:
    """
    Deterministic MVP gap scoring.

    - Health findings are assigned to Hutchins
    - Non-health findings are assigned to partner referrals and create ReferralOpportunity rows
    """
    GapFinding.objects.filter(submission=submission).delete()
    ReferralOpportunity.objects.filter(submission=submission).delete()

    def add_finding(*, category: str, severity: str, title: str, description: str) -> GapFinding:
        assigned_to = "hutchins" if category == "health" else "partner_referral"
        points = SEVERITY_POINTS[severity]
        return GapFinding.objects.create(
            submission=submission,
            customer=submission.customer,
            finding_type=category,
            category=category,
            severity=severity,
            points=points,
            title=title,
            description=description,
            explanation=description,
            status="open",
            assigned_to=assigned_to,
        )

    created_findings: list[GapFinding] = []
    created_referrals: list[ReferralOpportunity] = []
    household_members = list(submission.household_members.all())
    members_needing_coverage = [member for member in household_members if member.needs_coverage]
    members_with_prescriptions = [member for member in household_members if member.takes_prescriptions]
    members_with_other_coverage = [member for member in household_members if member.other_coverage_access]
    tobacco_users = [member for member in household_members if member.tobacco_user]

    current_health_coverage = (answers.get("current_health_coverage") or "").strip().lower()
    has_preferred_doctors = _as_bool(answers.get("has_preferred_doctors"))
    want_marketplace_help = _as_bool(answers.get("want_marketplace_help"))
    want_medicare_help = _as_bool(answers.get("want_medicare_help"))

    if current_health_coverage == "none" and members_needing_coverage:
        created_findings.append(
            add_finding(
                category="health",
                severity="critical",
                title="Household members need coverage with no current health plan",
                description="At least one household member needs coverage and the household reports no current health plan.",
            )
        )
        if members_with_prescriptions:
            created_findings.append(
                add_finding(
                    category="health",
                    severity="critical",
                    title="Prescriptions without health coverage",
                    description="One or more household members take prescription medications but the household reports no current health plan.",
                )
            )

    if members_with_prescriptions:
        prescription_names = ", ".join(member.first_name for member in members_with_prescriptions[:3])
        created_findings.append(
            add_finding(
                category="health",
                severity="medium",
                title="Medication and formulary review needed",
                description=f"Prescription medications were reported for: {prescription_names}. Review formulary and pharmacy access.",
            )
        )

    if want_marketplace_help:
        created_findings.append(
            add_finding(
                category="health",
                severity="medium",
                title="Marketplace / ACA follow-up requested",
                description="Client requested help reviewing Marketplace / ACA options and eligibility.",
            )
        )

    if want_medicare_help:
        created_findings.append(
            add_finding(
                category="health",
                severity="medium",
                title="Medicare follow-up requested",
                description="Client requested help reviewing Medicare options and timelines.",
            )
        )

    if has_preferred_doctors and current_health_coverage not in {"", "none"}:
        created_findings.append(
            add_finding(
                category="health",
                severity="low",
                title="Preferred doctors/facilities to keep in-network",
                description="Client has preferred doctors/facilities. Confirm networks and plan fit during review.",
            )
        )

    if members_with_other_coverage:
        created_findings.append(
            add_finding(
                category="health",
                severity="low",
                title="Other coverage eligibility coordination needed",
                description="At least one household member may have access to other coverage through a job, Medicare, Medicaid, or CHIP.",
            )
        )

    if tobacco_users:
        created_findings.append(
            add_finding(
                category="health",
                severity="low",
                title="Tobacco use noted for household",
                description="One or more household members report tobacco use. This should be reviewed during health quote preparation.",
            )
        )

    has_dependents = _as_bool(answers.get("has_dependents")) or submission.household_members.filter(role="dependent").exists()
    anyone_depends_on_income_or_care = _as_bool(answers.get("anyone_depends_on_income_or_care"))
    has_life_insurance = _as_bool(answers.get("has_life_insurance"))
    has_mortgage_or_major_debt = _as_bool(answers.get("has_mortgage_or_major_debt"))
    income_would_be_hard_to_replace = _as_bool(answers.get("income_would_be_hard_to_replace"))
    wants_life_referral = _as_bool(answers.get("wants_life_referral"))

    if (has_dependents or anyone_depends_on_income_or_care) and not has_life_insurance:
        created_findings.append(
            add_finding(
                category="life",
                severity="high",
                title="Life coverage gap: dependents/income reliance without life insurance",
                description="Client reports dependents or income/care reliance and no life insurance. Consider referral to a licensed partner agent.",
            )
        )

    if has_mortgage_or_major_debt and not has_life_insurance:
        created_findings.append(
            add_finding(
                category="life",
                severity="high" if income_would_be_hard_to_replace else "medium",
                title="Life coverage gap: debt exposure without life insurance",
                description="Client reports mortgage/major debt and no life insurance. Consider referral to a licensed partner agent.",
            )
        )

    if wants_life_referral:
        created_findings.append(
            add_finding(
                category="life",
                severity="medium",
                title="Requested life coverage review",
                description="Client requested to be connected with a licensed partner agent to discuss life coverage.",
            )
        )

    owns_home = _as_bool(answers.get("owns_home"))
    has_home_insurance = _as_bool(answers.get("has_home_insurance"))
    owns_rental_property = _as_bool(answers.get("owns_rental_property"))
    wants_home_referral = _as_bool(answers.get("wants_home_referral"))

    if owns_home and not has_home_insurance:
        created_findings.append(
            add_finding(
                category="home",
                severity="high",
                title="Homeowner without homeowners insurance",
                description="Client reports owning a home but no homeowners insurance. Consider referral opportunity.",
            )
        )

    if owns_rental_property:
        created_findings.append(
            add_finding(
                category="home",
                severity="medium",
                title="Rental property ownership",
                description="Client reports owning rental property. Consider referral for property/umbrella review.",
            )
        )

    if wants_home_referral:
        created_findings.append(
            add_finding(
                category="home",
                severity="medium",
                title="Requested home coverage review",
                description="Client requested to be connected with a licensed partner agent to review home coverage.",
            )
        )

    owns_or_drives_vehicle = _as_bool(answers.get("owns_or_drives_vehicle"))
    has_umbrella = _as_bool(answers.get("has_umbrella"))
    has_auto_insurance = _as_bool(answers.get("has_auto_insurance"))
    auto_liability_limit = (answers.get("auto_liability_limit") or "").strip().lower()
    teen_driver_in_household = _as_bool(answers.get("teen_driver_in_household"))
    wants_auto_referral = _as_bool(answers.get("wants_auto_referral"))

    if owns_or_drives_vehicle and not has_auto_insurance:
        created_findings.append(
            add_finding(
                category="auto",
                severity="critical",
                title="No auto insurance reported",
                description="Client owns or drives a vehicle but reports no auto insurance. Consider referral opportunity.",
            )
        )

    if has_auto_insurance and auto_liability_limit in {"unknown", "state_minimum", "low"}:
        created_findings.append(
            add_finding(
                category="auto",
                severity="high" if teen_driver_in_household and auto_liability_limit in {"unknown", "low"} else "medium",
                title="Auto liability limits uncertain/low",
                description="Client has auto coverage but liability limits are unknown/state minimum/low. Consider referral opportunity.",
            )
        )

    if wants_auto_referral:
        created_findings.append(
            add_finding(
                category="auto",
                severity="medium",
                title="Requested auto coverage review",
                description="Client requested to be connected with a licensed partner agent to review auto coverage.",
            )
        )

    assets_over_250k = _as_bool(answers.get("assets_over_250k"))
    has_extra_liability_risk = _as_bool(answers.get("has_extra_liability_risk"))
    wants_umbrella_referral = _as_bool(answers.get("wants_umbrella_referral"))

    if assets_over_250k and not has_umbrella:
        created_findings.append(
            add_finding(
                category="umbrella",
                severity="high",
                title="Assets over $250k without umbrella coverage",
                description="Client reports assets over $250k and no umbrella coverage. Consider referral opportunity.",
            )
        )

    if has_extra_liability_risk and not has_umbrella:
        created_findings.append(
            add_finding(
                category="umbrella",
                severity="high" if assets_over_250k else "medium",
                title="Extra liability risk without umbrella coverage",
                description="Client reports extra liability risks and no umbrella coverage. Consider referral opportunity.",
            )
        )

    if wants_umbrella_referral:
        created_findings.append(
            add_finding(
                category="umbrella",
                severity="medium",
                title="Requested umbrella coverage review",
                description="Client requested to be connected with a licensed partner agent to review umbrella coverage.",
            )
        )

    # Create referrals for non-health findings
    for finding in created_findings:
        if finding.category == "health":
            continue
        if finding.severity not in {"critical", "high", "medium"}:
            continue
        created_referrals.append(
            ReferralOpportunity.objects.create(
                submission=submission,
                customer=submission.customer,
                category=finding.category,
                severity=finding.severity,
                status="possible_opportunity",
                notes=finding.title,
            )
        )

    total_points = sum(f.points for f in created_findings)
    coverage_score = max(0, 100 - total_points)

    # touch updated_at for convenience in dashboards
    submission.updated_at = timezone.now()
    submission.save(update_fields=["updated_at"])

    return ScoringResult(total_points=total_points, coverage_score=coverage_score, findings=created_findings, referrals=created_referrals)
