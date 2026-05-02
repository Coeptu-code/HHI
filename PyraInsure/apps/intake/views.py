from __future__ import annotations

import json
import secrets
from datetime import date

import requests
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.customers.models import CustomerRecord
from apps.customers.services import record_admin_event, record_intake_event
from apps.customers.services import build_submission_analysis_payload
from apps.gap_scoring.models import GapFinding
from apps.gap_scoring.services import build_coveragap_score
from apps.intake.conversation import build_turns, find_current_turn
from apps.intake.forms import (
    BasicInfoForm,
    ConsentForm,
    HouseholdCoverageNeedsForm,
    HouseholdMemberForm,
    PrescriptionCheckForm,
    PrescriptionMedicationForm,
    StepQuestionForm,
)
from apps.intake.models import HouseholdMember, IntakeAnswer, IntakeSubmission, PrescriptionMedication
from apps.intake.questions import QUESTION_BANK, STEP_LABELS, get_step_questions, get_visible_steps
from apps.intake.services import analyze_intake_session
from apps.intake.services.intake_normalization import (
    detect_possible_full_name,
    normalize_date,
    normalize_email,
    normalize_income,
    normalize_liability_limit,
    normalize_name,
    normalize_phone,
    normalize_state,
    normalize_yes_no,
    normalize_zip,
    split_full_name,
)
from apps.intake.services.address_lookup import get_address_provider, normalize_address_input
from apps.questionnaires.models import QuestionnaireLink
from apps.referrals.models import ReferralOpportunity


HOUSEHOLD_HELPERS = [
    "Do not include a baby as a dependent until the baby is born.",
    "Tobacco user means used tobacco products 4 or more times per week on average during the past 6 months, not including ceremonial uses.",
    "Other coverage access means eligible for health coverage through a job, Medicare, Medicaid, or CHIP.",
]

RXTERMS_SEARCH_URL = "https://clinicaltables.nlm.nih.gov/api/rxterms/v3/search"

TURN_TO_QUESTION_KEY: dict[str, str] = {
    "first_name": "first_name",
    "last_name": "last_name",
    "dob": "primary_date_of_birth",
    "street_address": "street_address",
    "zip_code": "zip_code",
    "state": "state",
    "preferred_contact_method": "preferred_contact_method",
    "phone": "phone",
    "email": "email",
    "main_concern": "main_concern",
    "health_coverage": "current_health_coverage",
    "health_doctors": "has_preferred_doctors",
    "health_marketplace": "want_marketplace_help",
    "health_medicare": "want_medicare_help",
    "health_income": "estimated_household_income",
    "life_dependents": "anyone_depends_on_income_or_care",
    "life_has_insurance": "has_life_insurance",
    "life_mortgage": "has_mortgage_or_major_debt",
    "life_income_replace": "income_would_be_hard_to_replace",
    "auto_owns_vehicle": "owns_or_drives_vehicle",
    "auto_has_insurance": "has_auto_insurance",
    "auto_liability": "auto_liability_limit",
    "auto_teen_driver": "teen_driver_in_household",
    "home_owns": "owns_home",
    "home_has_insurance": "has_home_insurance",
    "home_rental": "owns_rental_property",
    "umbrella_has": "has_umbrella",
    "umbrella_assets": "assets_over_250k",
    "umbrella_risk": "has_extra_liability_risk",
    "wants_life_referral": "wants_life_referral",
    "wants_auto_referral": "wants_auto_referral",
    "wants_home_referral": "wants_home_referral",
    "wants_umbrella_referral": "wants_umbrella_referral",
}


def _wizard_session_key(token: str) -> str:
    return f"intake_wizard_{token}"


def _get_wizard_data(request: HttpRequest, token: str) -> dict:
    key = _wizard_session_key(token)
    data = request.session.get(key)
    if not data:
        data = {
            "basic_info": {},
            "household_members": [],
            "answers": {},
            "consents": {},
            "prescriptions": {},
        }
        request.session[key] = data
    data.setdefault("basic_info", {})
    data.setdefault("household_members", [])
    data.setdefault("answers", {})
    data.setdefault("consents", {})
    data.setdefault("prescriptions", {})
    return data


def _save_wizard_data(request: HttpRequest, token: str, data: dict) -> None:
    request.session[_wizard_session_key(token)] = data
    request.session.modified = True


def _clear_wizard_data(request: HttpRequest, token: str) -> None:
    key = _wizard_session_key(token)
    if key in request.session:
        del request.session[key]
        request.session.modified = True


def _generate_score_access_token() -> str:
    while True:
        score_token = secrets.token_urlsafe(32)
        if not IntakeSubmission.objects.filter(score_access_token=score_token).exists():
            return score_token


def _serialize_value(value: object) -> str | bool | int:
    if isinstance(value, bool):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, date):
        return value.isoformat()
    return str(value or "")


def _stringify_answer(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()  # type: ignore[attr-defined]
        except Exception:
            pass
    return str(value)


def _bool_from_session(value: object, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _normalized_answer_payload(
    *,
    raw_value: object,
    normalized_value: object,
    display_value: object | None = None,
    validation_status: str = "validated",
    confidence: float | None = None,
    metadata: dict | None = None,
) -> dict:
    return {
        "raw_value": _stringify_answer(raw_value),
        "normalized_value": normalized_value,
        "display_value": _stringify_answer(display_value if display_value is not None else normalized_value),
        "validation_status": validation_status,
        "confidence": confidence,
        "metadata": metadata or {},
    }


def _store_normalized_answer(
    data: dict,
    *,
    question_key: str,
    raw_value: object,
    normalized_value: object,
    display_value: object | None = None,
    validation_status: str = "validated",
    confidence: float | None = None,
    metadata: dict | None = None,
) -> None:
    raw_answers = data.setdefault("_raw_answers", {})
    normalized_answers = data.setdefault("_normalized_answers", {})
    raw_answers[question_key] = _stringify_answer(raw_value)
    normalized_answers[question_key] = _normalized_answer_payload(
        raw_value=raw_value,
        normalized_value=normalized_value,
        display_value=display_value,
        validation_status=validation_status,
        confidence=confidence,
        metadata=metadata,
    )


def _evaluate_turn_messages(turn, data: dict) -> list[str]:
    messages: list[str] = []
    for msg in turn.avery_messages:
        if callable(msg):
            messages.append(str(msg(data)))
        else:
            messages.append(str(msg))
    return messages


def _append_chat_exchange(data: dict, *, avery_messages: list[str], user_display: str | None) -> None:
    history = data.setdefault("chat_history", [])
    for message in avery_messages:
        history.append({"role": "avery", "text": message})
    if user_display:
        history.append({"role": "user", "text": user_display})


def _run_address_lookup(*, street_address: str, zip_code: str, state: str) -> dict:
    provider = get_address_provider()
    normalized_street = normalize_address_input(street_address)
    result = provider.lookup_address(normalized_street, zip_code=zip_code or None, state=state or None)
    status = str(result.get("status") or "no_match")
    suggestions = result.get("suggestions") or []
    if not isinstance(suggestions, list):
        suggestions = []
    return {
        "status": status,
        "suggestions": suggestions,
        "normalized_street": normalized_street,
    }


def _first_name_confirmation_turn(full_name: str) -> dict:
    first_name, _ = split_full_name(full_name)
    return {
        "id": "first_name_confirm",
        "avery_messages": [
            f"Just to confirm — is '{full_name}' your full name, or is your first name {first_name}?"
        ],
        "input": {
            "type": "chips",
            "chips": [
                {"label": "That's my full name", "value": "__full_name__"},
                {"label": f"Just {first_name}", "value": "__just_first__"},
                {"label": "Re-enter", "value": "__reenter__"},
            ],
            "placeholder": "",
            "card_type": "",
        },
    }


def _address_confirmation_turn(suggestions: list[dict], *, status: str) -> dict:
    if status == "multiple_matches":
        prompt = "I found a few close matches. Which one looks right?"
    else:
        top = suggestions[0] if suggestions else {}
        prompt = f"Did you mean {top.get('street', top.get('formatted', 'this address'))}?"

    chips = []
    for index, suggestion in enumerate(suggestions[:3]):
        chips.append({
            "label": suggestion.get("formatted") or suggestion.get("street") or f"Option {index + 1}",
            "value": f"__address_select_{index}__",
        })
    chips.append({"label": "No, I'll re-enter it", "value": "__address_reenter__"})

    return {
        "id": "address_confirm",
        "avery_messages": [prompt],
        "input": {
            "type": "address_suggestions",
            "chips": chips,
            "placeholder": "",
            "card_type": "",
        },
    }


def _pending_clarification_turn(data: dict) -> dict | None:
    address_pending = data.get("_pending_address_lookup") or {}
    suggestions = address_pending.get("suggestions") if isinstance(address_pending, dict) else None
    if suggestions:
        status = str(address_pending.get("status") or "needs_confirmation")
        return _address_confirmation_turn(list(suggestions), status=status)

    pending_full_name = str(data.get("_pending_full_name") or "").strip()
    if pending_full_name:
        return _first_name_confirmation_turn(pending_full_name)
    return None


def _get_active_link(token: str) -> QuestionnaireLink:
    link = get_object_or_404(QuestionnaireLink, token=token)
    if not link.can_use():
        raise Http404("This intake link is no longer active.")
    return link


def _track_intake_link_open(link: QuestionnaireLink) -> None:
    newly_started = False
    link.open_count = (link.open_count or 0) + 1
    link.last_opened_at = timezone.now()
    update_fields = ["open_count", "last_opened_at"]
    if link.status in {"created", "sent"}:
        link.status = "started"
        if link.started_at is None:
            link.started_at = timezone.now()
            newly_started = True
            update_fields.append("started_at")
        update_fields.append("status")
    link.save(update_fields=update_fields)
    if link.customer_id and newly_started:
        record_intake_event(
            customer_id=link.customer_id,
            activity_type="intake_started",
            title="Avery intake started",
            metadata={"link_id": link.id, "open_count": link.open_count},
            intake_session_id=None,
        )


def _get_visible_steps_for_data(link: QuestionnaireLink, data: dict) -> list[str]:
    steps = list(get_visible_steps(link.selected_modules()))
    if "health" not in link.selected_modules():
        return steps

    prescription_steps = [
        f"prescription_{member['temp_id']}"
        for member in data.get("household_members", [])
        if _bool_from_session(member.get("takes_prescriptions"))
    ]
    insert_at = steps.index("prescription_check") + 1
    return steps[:insert_at] + prescription_steps + steps[insert_at:]


def _get_step_meta(link: QuestionnaireLink, data: dict, current_step: str) -> dict:
    steps = _get_visible_steps_for_data(link, data)
    if current_step not in steps:
        raise Http404("This step is not available for the selected intake.")
    index = steps.index(current_step)
    return {
        "steps": steps,
        "step": current_step,
        "step_label": _get_step_label(data, current_step),
        "step_index": index + 1,
        "step_total": len(steps),
        "previous_step": steps[index - 1] if index > 0 else None,
        "next_step": steps[index + 1] if index < len(steps) - 1 else None,
    }


def _get_step_label(data: dict, step: str) -> str:
    if step.startswith("prescription_"):
        member = _find_household_member(data, step.removeprefix("prescription_"))
        if member:
            return f"Prescriptions for {_member_label(member)}"
        return "Prescription Entry"
    return STEP_LABELS.get(step, step.replace("_", " ").title())


def _member_label(member: dict) -> str:
    name = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
    role = member.get("role")
    suffix = {"primary": " (You)", "spouse": " (Spouse)", "dependent": " (Dependent)"}.get(role, "")
    return f"{name}{suffix}".strip()


def _sync_primary_household_member(data: dict) -> None:
    basic = data.get("basic_info", {})
    if not basic:
        return

    primary_existing = _find_household_member(data, "primary") or {}
    primary_member = {
        "temp_id": "primary",
        "role": "primary",
        "first_name": basic.get("first_name", ""),
        "last_name": basic.get("last_name", ""),
        "date_of_birth": basic.get("primary_date_of_birth", ""),
        "needs_coverage": primary_existing.get("needs_coverage", True),
        "other_coverage_access": primary_existing.get("other_coverage_access", False),
        "legal_parent_guardian_under_19": primary_existing.get("legal_parent_guardian_under_19", False),
        "claimed_tax_dependent": primary_existing.get("claimed_tax_dependent", False),
        "pregnant": primary_existing.get("pregnant", False),
        "tobacco_user": primary_existing.get("tobacco_user", False),
        "takes_prescriptions": primary_existing.get("takes_prescriptions", False),
    }

    members = [member for member in data.get("household_members", []) if member.get("temp_id") != "primary"]
    data["household_members"] = [primary_member] + members


def _household_initial(member: dict | None = None) -> dict:
    if not member:
        return {"needs_coverage": True}
    return {
        "first_name": member.get("first_name", ""),
        "last_name": member.get("last_name", ""),
        "date_of_birth": member.get("date_of_birth", ""),
        "needs_coverage": _bool_from_session(member.get("needs_coverage"), True),
        "other_coverage_access": _bool_from_session(member.get("other_coverage_access")),
        "legal_parent_guardian_under_19": _bool_from_session(member.get("legal_parent_guardian_under_19")),
        "claimed_tax_dependent": _bool_from_session(member.get("claimed_tax_dependent")),
        "pregnant": _bool_from_session(member.get("pregnant")),
        "tobacco_user": _bool_from_session(member.get("tobacco_user")),
        "takes_prescriptions": _bool_from_session(member.get("takes_prescriptions")),
    }


def _find_household_member(data: dict, temp_id: str) -> dict | None:
    for member in data.get("household_members", []):
        if member.get("temp_id") == temp_id:
            return member
    return None


def _upsert_household_member(data: dict, temp_id: str | None, role: str, cleaned_data: dict) -> None:
    members = data.get("household_members", [])
    existing_member = _find_household_member(data, temp_id) if temp_id else None
    payload = {
        "temp_id": temp_id or f"member-{secrets.token_hex(4)}",
        "role": role,
        "first_name": cleaned_data["first_name"],
        "last_name": cleaned_data.get("last_name", ""),
        "date_of_birth": cleaned_data["date_of_birth"].isoformat(),
        "needs_coverage": bool(cleaned_data.get("needs_coverage")),
        "other_coverage_access": bool(cleaned_data.get("other_coverage_access")),
        "legal_parent_guardian_under_19": bool(cleaned_data.get("legal_parent_guardian_under_19")),
        "claimed_tax_dependent": bool(cleaned_data.get("claimed_tax_dependent")),
        "pregnant": bool(cleaned_data.get("pregnant")),
        "tobacco_user": bool(cleaned_data.get("tobacco_user")),
        "takes_prescriptions": bool(existing_member.get("takes_prescriptions")) if existing_member else False,
    }

    updated = False
    for index, member in enumerate(members):
        if member.get("temp_id") == payload["temp_id"]:
            members[index] = payload
            updated = True
            break

    if not updated:
        if role == "spouse":
            members = [member for member in members if member.get("role") != "spouse"]
        members.append(payload)

    members.sort(key=lambda item: {"primary": 0, "spouse": 1, "dependent": 2}.get(item.get("role", ""), 9))
    data["household_members"] = members


def _serialize_form_data(cleaned_data: dict) -> dict:
    return {key: _serialize_value(value) for key, value in cleaned_data.items()}


def _get_form_initial(data: dict, section: str) -> dict:
    return dict(data.get(section, {}))


def _build_answer_map(data: dict, household_members: list[dict]) -> dict[str, object]:
    answer_map: dict[str, object] = {}
    answer_map.update(data.get("basic_info", {}))
    answer_map.update(data.get("answers", {}))
    answer_map["has_dependents"] = any(member.get("role") == "dependent" for member in household_members)
    answer_map["dependent_count"] = sum(1 for member in household_members if member.get("role") == "dependent")
    answer_map["has_prescriptions"] = any(_bool_from_session(member.get("takes_prescriptions")) for member in household_members)
    return answer_map


def _coverage_form_initial(household_members: list[dict]) -> dict:
    initial: dict[str, str] = {}
    for member in household_members:
        temp_id = member["temp_id"]
        initial[f"needs_coverage__{temp_id}"] = "yes" if _bool_from_session(member.get("needs_coverage"), True) else "no"
        initial[f"other_coverage_access__{temp_id}"] = "yes" if _bool_from_session(member.get("other_coverage_access")) else "no"
        initial[f"tobacco_user__{temp_id}"] = "yes" if _bool_from_session(member.get("tobacco_user")) else "no"
    return initial


def _apply_coverage_form_to_members(household_members: list[dict], cleaned_data: dict) -> None:
    for member in household_members:
        temp_id = member["temp_id"]
        member["needs_coverage"] = cleaned_data.get(f"needs_coverage__{temp_id}") == "yes"
        member["other_coverage_access"] = cleaned_data.get(f"other_coverage_access__{temp_id}") == "yes"
        member["tobacco_user"] = cleaned_data.get(f"tobacco_user__{temp_id}") == "yes"


def _prescription_check_initial(household_members: list[dict]) -> dict:
    initial: dict[str, str] = {}
    for member in household_members:
        temp_id = member["temp_id"]
        initial[f"takes_prescriptions__{temp_id}"] = "yes" if _bool_from_session(member.get("takes_prescriptions")) else "no"
    return initial


def _apply_prescription_check_to_members(data: dict, cleaned_data: dict) -> None:
    active_temp_ids: set[str] = set()
    for member in data.get("household_members", []):
        temp_id = member["temp_id"]
        takes = cleaned_data.get(f"takes_prescriptions__{temp_id}") == "yes"
        member["takes_prescriptions"] = takes
        if takes:
            active_temp_ids.add(temp_id)

    prescriptions = data.get("prescriptions", {})
    for temp_id in list(prescriptions.keys()):
        if temp_id not in active_temp_ids:
            prescriptions.pop(temp_id, None)
    for temp_id in active_temp_ids:
        prescriptions.setdefault(temp_id, [])
    data["prescriptions"] = prescriptions


def _coverage_member_rows(form: HouseholdCoverageNeedsForm, household_members: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for member in household_members:
        temp_id = member["temp_id"]
        rows.append(
            {
                "label": _member_label(member),
                "needs_coverage_field": form[f"needs_coverage__{temp_id}"],
                "other_coverage_access_field": form[f"other_coverage_access__{temp_id}"],
                "tobacco_user_field": form[f"tobacco_user__{temp_id}"],
            }
        )
    return rows


def _prescription_check_rows(form: PrescriptionCheckForm, household_members: list[dict]) -> list[dict]:
    rows: list[dict] = []
    for member in household_members:
        temp_id = member["temp_id"]
        rows.append(
            {
                "label": _member_label(member),
                "field": form[f"takes_prescriptions__{temp_id}"],
            }
        )
    return rows


def _get_prescriptions_for_member(data: dict, temp_id: str) -> list[dict]:
    return list(data.get("prescriptions", {}).get(temp_id, []))


def _set_prescriptions_for_member(data: dict, temp_id: str, medications: list[dict]) -> None:
    prescriptions = data.get("prescriptions", {})
    prescriptions[temp_id] = medications
    data["prescriptions"] = prescriptions


def intake_entry(request: HttpRequest, token: str) -> HttpResponse:
    link = _get_active_link(token)
    _track_intake_link_open(link)
    data = _get_wizard_data(request, token)
    _sync_primary_household_member(data)

    if request.method == "POST":
        data["_consent_given"] = True
        data.setdefault("consent", {}).update({
            "terms": request.POST.get("consent_terms") == "1",
            "privacy": request.POST.get("consent_terms") == "1",
            "contact": request.POST.get("consent_contact") == "1",
            "referral_sharing": request.POST.get("consent_referral_sharing") == "1",
        })
        _save_wizard_data(request, token, data)
        return redirect("intake_messenger", token=token)

    _save_wizard_data(request, token, data)
    return render(request, "intake/welcome.html", {"link": link})


def intake_step(request: HttpRequest, token: str, step: str) -> HttpResponse:
    link = _get_active_link(token)
    data = _get_wizard_data(request, token)
    _sync_primary_household_member(data)
    step_meta = _get_step_meta(link, data, step)

    if step == "basic":
        questions = get_step_questions("basic", link.selected_modules())
        if request.method == "POST":
            form = BasicInfoForm(questions, request.POST)
            if form.is_valid():
                data["basic_info"] = _serialize_form_data(form.cleaned_data)
                _sync_primary_household_member(data)
                _save_wizard_data(request, token, data)
                return redirect("intake_step", token=token, step=step_meta["next_step"])
        else:
            form = BasicInfoForm(questions, initial=_get_form_initial(data, "basic_info"))
        return render(request, "intake/step_basic.html", {"link": link, "form": form, **step_meta})

    if step == "household":
        _save_wizard_data(request, token, data)
        if request.method == "POST":
            target = step_meta["previous_step"] if request.POST.get("nav") == "previous" else step_meta["next_step"]
            return redirect("intake_step", token=token, step=target)
        return render(
            request,
            "intake/step_household.html",
            {
                "link": link,
                "household_members": data.get("household_members", []),
                "member_form": None,
                "member_role": None,
                "member_action_url": None,
                "editing_member": None,
                "helper_texts": HOUSEHOLD_HELPERS,
                **step_meta,
            },
        )

    if step == "household_coverage":
        household_members = data.get("household_members", [])
        if request.method == "POST":
            form = HouseholdCoverageNeedsForm(household_members, request.POST)
            if form.is_valid():
                _apply_coverage_form_to_members(household_members, form.cleaned_data)
                data["household_members"] = household_members
                _save_wizard_data(request, token, data)
                target = step_meta["previous_step"] if request.POST.get("nav") == "previous" else step_meta["next_step"]
                return redirect("intake_step", token=token, step=target)
        else:
            form = HouseholdCoverageNeedsForm(household_members, initial=_coverage_form_initial(household_members))
        return render(
            request,
            "intake/step_household_coverage.html",
            {
                "link": link,
                "household_members": household_members,
                "form": form,
                "member_rows": _coverage_member_rows(form, household_members),
                **step_meta,
            },
        )

    if step == "prescription_check":
        household_members = data.get("household_members", [])
        if request.method == "POST":
            form = PrescriptionCheckForm(household_members, request.POST)
            if form.is_valid():
                _apply_prescription_check_to_members(data, form.cleaned_data)
                _save_wizard_data(request, token, data)
                refreshed_meta = _get_step_meta(link, data, step)
                target = refreshed_meta["previous_step"] if request.POST.get("nav") == "previous" else refreshed_meta["next_step"]
                return redirect("intake_step", token=token, step=target)
        else:
            form = PrescriptionCheckForm(household_members, initial=_prescription_check_initial(household_members))
        return render(
            request,
            "intake/step_prescription_check.html",
            {
                "link": link,
                "household_members": household_members,
                "form": form,
                "member_rows": _prescription_check_rows(form, household_members),
                **step_meta,
            },
        )

    if step.startswith("prescription_"):
        member_temp_id = step.removeprefix("prescription_")
        member = _find_household_member(data, member_temp_id)
        if not member or not _bool_from_session(member.get("takes_prescriptions")):
            raise Http404("Prescription page is not available for this household member.")

        medications = _get_prescriptions_for_member(data, member_temp_id)
        form = PrescriptionMedicationForm()
        action = request.POST.get("action") if request.method == "POST" else None
        if request.method == "POST":
            if action == "add_medication":
                form = PrescriptionMedicationForm(request.POST)
                if form.is_valid():
                    cleaned = form.cleaned_data
                    drug_name = (cleaned.get("selected_drug_name") or cleaned.get("drug_search") or "").strip()
                    normalized_name = (cleaned.get("normalized_drug_name") or drug_name).strip()
                    medications.append(
                        {
                            "drug_id": (cleaned.get("selected_drug_id") or "").strip(),
                            "drug_name": drug_name,
                            "normalized_drug_name": normalized_name,
                            "source": (cleaned.get("source") or ("rxterms" if cleaned.get("selected_drug_id") else "manual")).strip(),
                            "dosage_strength": (cleaned.get("dosage_strength") or "").strip(),
                            "frequency": (cleaned.get("frequency") or "").strip(),
                        }
                    )
                    _set_prescriptions_for_member(data, member_temp_id, medications)
                    _save_wizard_data(request, token, data)
                    form = PrescriptionMedicationForm()
            elif action == "remove_medication":
                remove_index_raw = request.POST.get("remove_index", "")
                try:
                    remove_index = int(remove_index_raw)
                except ValueError:
                    remove_index = -1
                if 0 <= remove_index < len(medications):
                    medications.pop(remove_index)
                    _set_prescriptions_for_member(data, member_temp_id, medications)
                    _save_wizard_data(request, token, data)
            elif action == "previous":
                return redirect("intake_step", token=token, step=step_meta["previous_step"])
            elif action == "next":
                return redirect("intake_step", token=token, step=step_meta["next_step"])

        return render(
            request,
            "intake/step_prescription_entry.html",
            {
                "link": link,
                "member": member,
                "form": form,
                "medications": medications,
                **step_meta,
            },
        )

    if step == "consent":
        if request.method == "POST":
            form = ConsentForm(request.POST)
            if form.is_valid():
                data["consents"] = _serialize_form_data(form.cleaned_data)
                _save_wizard_data(request, token, data)
                if request.POST.get("nav") == "previous" and step_meta["previous_step"]:
                    return redirect("intake_step", token=token, step=step_meta["previous_step"])
                return redirect("intake_submit", token=token)
        else:
            form = ConsentForm(initial=_get_form_initial(data, "consents"))
        return render(request, "intake/step_consent.html", {"link": link, "form": form, **step_meta})

    questions = get_step_questions(step, link.selected_modules())
    if request.method == "POST":
        form = StepQuestionForm(questions, request.POST)
        if form.is_valid():
            answers = data.get("answers", {})
            answers.update(_serialize_form_data(form.cleaned_data))
            data["answers"] = answers
            _save_wizard_data(request, token, data)
            target = step_meta["previous_step"] if request.POST.get("nav") == "previous" else step_meta["next_step"]
            return redirect("intake_step", token=token, step=target)
    else:
        form = StepQuestionForm(questions, initial=_get_form_initial(data, "answers"))

    template_name = "intake/step_health_coverage.html" if step == "health" else "intake/step_questions.html"
    return render(request, template_name, {"link": link, "form": form, **step_meta})


def intake_household_add_spouse(request: HttpRequest, token: str) -> HttpResponse:
    return _household_member_editor(request, token, role="spouse")


def intake_household_add_dependent(request: HttpRequest, token: str) -> HttpResponse:
    return _household_member_editor(request, token, role="dependent")


def intake_household_edit(request: HttpRequest, token: str, member_id: str) -> HttpResponse:
    return _household_member_editor(request, token, temp_id=member_id)


def _household_member_editor(
    request: HttpRequest,
    token: str,
    role: str | None = None,
    temp_id: str | None = None,
) -> HttpResponse:
    link = _get_active_link(token)
    data = _get_wizard_data(request, token)
    _sync_primary_household_member(data)
    step_meta = _get_step_meta(link, data, "household")

    member = _find_household_member(data, temp_id) if temp_id else None
    member_role = role or (member.get("role") if member else None)
    if member_role not in {"spouse", "dependent"}:
        raise Http404("Invalid household member.")

    if request.method == "POST":
        form = HouseholdMemberForm(request.POST)
        if form.is_valid():
            _upsert_household_member(data, temp_id=temp_id, role=member_role, cleaned_data=form.cleaned_data)
            _save_wizard_data(request, token, data)
            return redirect("intake_step", token=token, step="household")
    else:
        form = HouseholdMemberForm(initial=_household_initial(member))

    return render(
        request,
        "intake/step_household.html",
        {
            "link": link,
            "household_members": data.get("household_members", []),
            "member_form": form,
            "member_role": member_role,
            "member_action_url": request.path,
            "editing_member": member,
            "helper_texts": HOUSEHOLD_HELPERS,
            **step_meta,
        },
    )


def intake_household_delete(request: HttpRequest, token: str, member_id: str) -> HttpResponse:
    _get_active_link(token)
    if request.method != "POST":
        return redirect("intake_step", token=token, step="household")

    data = _get_wizard_data(request, token)
    data["household_members"] = [
        member
        for member in data.get("household_members", [])
        if member.get("temp_id") == "primary" or member.get("temp_id") != member_id
    ]
    data.get("prescriptions", {}).pop(member_id, None)
    _sync_primary_household_member(data)
    _save_wizard_data(request, token, data)
    return redirect("intake_step", token=token, step="household")


@transaction.atomic
def intake_submit(request: HttpRequest, token: str) -> HttpResponse:
    link = _get_active_link(token)
    data = _get_wizard_data(request, token)

    if request.method != "POST":
        return redirect("intake_step", token=token, step="consent")

    form = ConsentForm(request.POST)
    if not form.is_valid():
        step_meta = _get_step_meta(link, data, "consent")
        return render(request, "intake/step_consent.html", {"link": link, "form": form, **step_meta})

    data["consents"] = _serialize_form_data(form.cleaned_data)
    _sync_primary_household_member(data)
    _save_wizard_data(request, token, data)

    basic_info = data.get("basic_info", {})
    household_members = data.get("household_members", [])
    consents = data.get("consents", {})
    prescriptions = data.get("prescriptions", {})

    email = str(basic_info.get("email", "")).strip()
    phone = str(basic_info.get("phone", "")).strip()

    customer = None
    if email:
        customer = CustomerRecord.objects.filter(agent=link.agent, email__iexact=email).first()
    if customer is None and phone:
        customer = CustomerRecord.objects.filter(agent=link.agent, phone=phone).first()
    if customer is None:
        customer = CustomerRecord(agent=link.agent)

    customer.first_name = str(basic_info.get("first_name", "")).strip()
    customer.last_name = str(basic_info.get("last_name", "")).strip()
    customer.email = email
    customer.phone = phone
    customer.state = str(basic_info.get("state", "")).strip().upper()[:2]
    customer.preferred_contact_method = str(basic_info.get("preferred_contact_method", "")).strip()
    if customer.client_since is None:
        customer.client_since = timezone.localdate()
    customer.last_submission_at = timezone.now()
    customer.save()

    submission = IntakeSubmission.objects.create(
        questionnaire_link=link,
        agent=link.agent,
        customer=customer,
        public_token=link.token,
        source="questionnaire_link",
        consent_terms=bool(consents.get("consent_terms")),
        consent_privacy=bool(consents.get("consent_privacy")),
        consent_contact=bool(consents.get("consent_contact")),
        consent_referral_sharing=bool(consents.get("consent_referral_sharing")),
        status="in_progress",
        score_access_token=_generate_score_access_token(),
    )

    persisted_members: dict[str, HouseholdMember] = {}
    for member in household_members:
        if not member.get("date_of_birth"):
            continue
        persisted_member = HouseholdMember.objects.create(
            submission=submission,
            customer=customer,
            role=member.get("role", "dependent"),
            name=f"{member.get('first_name', '')} {member.get('last_name', '')}".strip(),
            first_name=member.get("first_name", ""),
            last_name=member.get("last_name", ""),
            date_of_birth=member["date_of_birth"],
            dob=member["date_of_birth"],
            needs_coverage=bool(member.get("needs_coverage")),
            needs_health_coverage=bool(member.get("needs_coverage")),
            other_coverage_access=bool(member.get("other_coverage_access")),
            legal_parent_guardian_under_19=bool(member.get("legal_parent_guardian_under_19")),
            claimed_tax_dependent=bool(member.get("claimed_tax_dependent")),
            pregnant=bool(member.get("pregnant")),
            tobacco_user=bool(member.get("tobacco_user")),
            takes_prescriptions=bool(member.get("takes_prescriptions")),
            has_prescriptions=bool(member.get("takes_prescriptions")),
        )
        persisted_members[member["temp_id"]] = persisted_member

    for temp_id, medication_rows in prescriptions.items():
        household_member = persisted_members.get(temp_id)
        if not household_member:
            continue
        for medication in medication_rows:
            PrescriptionMedication.objects.create(
                submission=submission,
                household_member=household_member,
                drug_id=medication.get("drug_id", ""),
                drug_name=medication.get("drug_name", ""),
                normalized_drug_name=medication.get("normalized_drug_name", ""),
                source=medication.get("source", "rxterms"),
                dosage_strength=medication.get("dosage_strength", ""),
                frequency=medication.get("frequency", ""),
            )

    answer_map = _build_answer_map(data, household_members)
    raw_answer_map = data.get("_raw_answers", {})
    normalized_answer_map = data.get("_normalized_answers", {})
    for step_name in _get_visible_steps_for_data(link, data):
        if step_name in {"household", "household_coverage", "prescription_check", "consent"} or step_name.startswith("prescription_"):
            continue
        for question in get_step_questions(step_name, link.selected_modules()):
            value = answer_map.get(question.key, "")
            raw_value = raw_answer_map.get(question.key, value)
            IntakeAnswer.objects.create(
                submission=submission,
                customer=customer,
                module=(question.supports[0] if question.supports else ""),
                supports=",".join(question.supports),
                question_key=question.key,
                question_text=question.text,
                answer_value=_stringify_answer(raw_value),
                normalized_value=normalized_answer_map.get(question.key),
            )

    submission.status = "submitted"
    submission.submitted_at = timezone.now()
    submission.save(update_fields=["status", "submitted_at", "updated_at"])

    record_intake_event(
        customer_id=customer.id,
        intake_session_id=submission.id,
        activity_type="intake_submitted",
        title="Intake submitted",
        metadata={"link_id": link.id},
    )

    link.completed_at = timezone.now()
    link.status = "submitted"
    link.customer = customer
    link.is_active = False
    link.save(update_fields=["completed_at", "is_active", "status", "customer"])

    analyze_intake_session(submission.id)
    _clear_wizard_data(request, token)
    return redirect("intake_thank_you", score_token=submission.score_access_token)


def intake_thank_you(request: HttpRequest, score_token: str | None = None) -> HttpResponse:
    score_url = None
    if score_token and IntakeSubmission.objects.filter(score_access_token=score_token).exists():
        score_url = reverse("coveragap_score", args=[score_token])
    return render(
        request,
        "intake/thank_you.html",
        {
            "score_url": score_url,
        },
    )


def coveragap_score_view(request: HttpRequest, score_token: str) -> HttpResponse:
    submission = (
        IntakeSubmission.objects.select_related("questionnaire_link", "customer")
        .filter(score_access_token=score_token, status="submitted")
        .first()
    )
    if submission is None:
        return render(
            request,
            "intake/coveragap_score.html",
            {
                "score_unavailable": True,
            },
            status=404,
        )

    submission.score_viewed_at = timezone.now()
    submission.save(update_fields=["score_viewed_at"])

    scorecard = build_coveragap_score(submission)
    return render(
        request,
        "intake/coveragap_score.html",
        {
            "scorecard": scorecard,
            "customer": submission.customer,
        },
    )


def drug_search(request: HttpRequest) -> JsonResponse:
    query = (request.GET.get("q") or "").strip()
    if len(query) < 2:
        return JsonResponse([], safe=False)

    try:
        # TODO: add short-lived caching to avoid repeated upstream lookups for the same term.
        response = requests.get(
            RXTERMS_SEARCH_URL,
            params={
                "terms": query,
                "ef": "STRENGTHS_AND_FORMS",
                "maxList": 10,
            },
            timeout=5,
        )
        response.raise_for_status()
        payload = response.json()
    except Exception:
        return JsonResponse([], safe=False)

    results: list[dict] = []
    if isinstance(payload, list) and len(payload) >= 4:
        ids = payload[1] if isinstance(payload[1], list) else []
        extras = payload[2] if isinstance(payload[2], dict) else {}
        displays = payload[3] if isinstance(payload[3], list) else []
        strengths = extras.get("STRENGTHS_AND_FORMS", []) if isinstance(extras, dict) else []

        for index, drug_id in enumerate(ids):
            display_name = displays[index] if index < len(displays) else str(drug_id)
            forms = strengths[index] if index < len(strengths) else []
            if isinstance(forms, str):
                forms = [forms]
            results.append(
                {
                    "id": str(drug_id),
                    "name": display_name,
                    "display_name": display_name,
                    "strengths_and_forms": forms,
                }
            )

    return JsonResponse(results, safe=False)


@login_required
def pre_call_summary(request: HttpRequest, submission_id: int) -> HttpResponse:
    submission = get_object_or_404(
        IntakeSubmission.objects.select_related("customer", "agent", "questionnaire_link"),
        id=submission_id,
    )
    if request.user.is_authenticated and submission.customer_id:
        record_admin_event(
            customer_id=submission.customer_id,
            intake_session_id=submission.id,
            activity_type="pre_call_summary_opened",
            title="Pre-call summary opened",
            actor_name=request.user.get_username(),
            dedupe_window_seconds=120,
        )

    findings = list(GapFinding.objects.filter(submission=submission).order_by("-points", "-created_at"))
    referrals = list(ReferralOpportunity.objects.filter(submission=submission).order_by("-updated_at"))
    answers = list(IntakeAnswer.objects.filter(submission=submission).order_by("id"))
    household_members = list(submission.household_members.order_by("created_at"))
    medications = list(
        PrescriptionMedication.objects.filter(submission=submission)
        .select_related("household_member")
        .order_by("household_member__created_at", "created_at")
    )

    total_points = sum(finding.points for finding in findings)
    coverage_score = max(0, 100 - total_points)
    gap_risk_score = total_points

    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for finding in findings:
        severity_counts[finding.severity] = severity_counts.get(finding.severity, 0) + 1

    health_findings = [finding for finding in findings if finding.category == "health"]
    partner_findings = [finding for finding in findings if finding.category != "health"]

    modules = submission.questionnaire_link.selected_modules()
    question_position = {question.key: question.position for question in QUESTION_BANK}
    answers.sort(key=lambda answer: question_position.get(answer.question_key, 10_000))

    referrals_by_category: dict[str, list[ReferralOpportunity]] = {}
    for referral in referrals:
        referrals_by_category.setdefault(referral.category, []).append(referral)

    medications_by_member_id: dict[int, list[PrescriptionMedication]] = {}
    for medication in medications:
        medications_by_member_id.setdefault(medication.household_member_id, []).append(medication)

    household_summaries: list[dict] = []
    for member in household_members:
        household_summaries.append(
            {
                "member": member,
                "medications": medications_by_member_id.get(member.id, []),
            }
        )

    talking_points = [finding.title for finding in findings[:6]]
    context = {
        "submission": submission,
        "customer": submission.customer,
        "modules": modules,
        "coverage_score": coverage_score,
        "gap_risk_score": gap_risk_score,
        "severity_counts": severity_counts,
        "health_findings": health_findings,
        "partner_findings": partner_findings,
        "referrals_by_category": referrals_by_category,
        "answers": answers,
        "household_members": household_members,
        "household_summaries": household_summaries,
        "talking_points": talking_points,
        "active_nav": "",
    }
    return render(request, "summaries/pre_call_summary.html", context)


@login_required
def analyze_intake_session_admin(request: HttpRequest, submission_id: int) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

    submission = get_object_or_404(
        IntakeSubmission.objects.select_related("agent__user", "customer"),
        id=submission_id,
        agent__user=request.user,
    )

    analysis_result = analyze_intake_session(submission.id)
    return JsonResponse(
        {
            "ok": True,
            "submission_id": submission.id,
            "finding_count": len(analysis_result.findings),
            "talking_point_count": len(analysis_result.talking_points),
            "referral_count": len(analysis_result.referrals),
            "raw_gap_score": analysis_result.raw_gap_score,
            "capped_gap_score": analysis_result.capped_gap_score,
        }
    )


@login_required
def submission_analysis(request: HttpRequest, submission_id: int) -> JsonResponse:
    submission = get_object_or_404(
        IntakeSubmission.objects.select_related("agent__user", "customer", "questionnaire_link"),
        id=submission_id,
        agent__user=request.user,
    )
    payload = build_submission_analysis_payload(submission)
    return JsonResponse(payload)


@login_required
def admin_submission_review(request: HttpRequest, submission_id: int) -> JsonResponse:
    if request.method != "PATCH":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

    submission = get_object_or_404(
        IntakeSubmission.objects.select_related("customer", "agent__user"),
        id=submission_id,
    )
    if not request.user.is_staff and submission.agent.user_id != request.user.id:
        return JsonResponse({"ok": False, "error": "Forbidden."}, status=403)

    body = json.loads(request.body or "{}")
    review_status = str(body.get("review_status") or "unreviewed")
    if review_status not in {"unreviewed", "reviewed", "needs_follow_up"}:
        return JsonResponse({"ok": False, "error": "Invalid review_status."}, status=400)

    submission.review_status = review_status
    submission.review_notes = str(body.get("review_notes") or "")
    submission.reviewed_at = timezone.now()
    submission.reviewed_by = request.user
    submission.save(update_fields=["review_status", "review_notes", "reviewed_at", "reviewed_by", "updated_at"])

    if submission.customer_id:
        if review_status == "needs_follow_up":
            submission.customer.status = "prospect"
            submission.customer.save(update_fields=["status", "updated_at"])
        record_admin_event(
            customer_id=submission.customer_id,
            intake_session_id=submission.id,
            activity_type="manual_review_completed",
            title="Manual review completed",
            actor_name=request.user.get_username(),
            description=submission.review_notes or None,
            metadata={"review_status": review_status},
        )

    return JsonResponse({"ok": True, "submission_id": submission.id, "review_status": submission.review_status})


# ── Messenger-style intake ────────────────────────────────────────

def intake_messenger(request: HttpRequest, token: str) -> HttpResponse:
    """Serve the messenger-style intake shell."""
    link = _get_active_link(token)
    data = _get_wizard_data(request, token)
    modules = link.selected_modules()

    # Build turns and find current
    turns = build_turns(data, modules)
    completed = set(data.get("_completed_turns", []))
    pending_turn = _pending_clarification_turn(data)
    current_turn = pending_turn or find_current_turn(turns, completed)

    if current_turn is None:
        # All turns completed - redirect to submit
        return redirect("intake_submit", token=token)

    # Get history
    history = data.get("chat_history", [])

    # Serialize current turn for initial render
    current_turn_data = current_turn if pending_turn else _serialize_turn(current_turn, data, link)
    progress_data = {"index": len(completed), "total": len(turns)}

    return render(request, "intake/messenger.html", {
        "link": link,
        "history_json": json.dumps(history),
        "current_turn": current_turn_data,
        "progress": progress_data,
    })


def intake_messenger_api(request: HttpRequest, token: str) -> JsonResponse:
    """JSON API for messenger conversation flow."""
    link = _get_active_link(token)
    data = _get_wizard_data(request, token)
    modules = link.selected_modules()

    turns = build_turns(data, modules)
    completed = set(data.get("_completed_turns", []))

    if request.method == "GET":
        # Return current state for page load
        pending_turn = _pending_clarification_turn(data)
        current_turn = pending_turn or find_current_turn(turns, completed)
        if current_turn is None:
            return JsonResponse({
                "history": data.get("chat_history", []),
                "current": None,
                "progress": {"index": len(turns), "total": len(turns)},
                "done": True,
                "redirect_url": reverse("intake_submit", args=[token]),
            })

        return JsonResponse({
            "history": data.get("chat_history", []),
            "current": current_turn if pending_turn else _serialize_turn(current_turn, data, link),
            "progress": {"index": len(completed), "total": len(turns)},
            "done": False,
        })

    # POST: process answer
    body_data = json.loads(request.body)
    turn_id = body_data.get("turn_id", "")
    answer = body_data.get("answer", "").strip()
    action = body_data.get("action", "")

    # Handle household member add/remove (special case)
    if action == "household_add":
        role = body_data.get("role", "")
        first_name = body_data.get("first_name", "").strip()
        last_name = body_data.get("last_name", "").strip()
        dob = body_data.get("date_of_birth", "").strip()
        return _handle_household_member_add(request, token, data, link, role, first_name, last_name, dob)

    if action == "household_remove":
        role = body_data.get("role", "")
        temp_id = body_data.get("temp_id", "")
        return _handle_household_member_remove(request, token, data, link, role, temp_id)

    # Handle prescription add/remove (special case)
    if action == "prescription_add":
        return _handle_prescription_add(request, token, data, link, body_data)

    if action == "prescription_remove":
        return _handle_prescription_remove(request, token, data, link, body_data)

    if turn_id == "address_confirm":
        pending = data.get("_pending_address_lookup") or {}
        suggestions = list(pending.get("suggestions") or [])
        if answer == "__address_reenter__":
            _append_chat_exchange(
                data,
                avery_messages=_address_confirmation_turn(suggestions, status=str(pending.get("status") or "needs_confirmation"))["avery_messages"],
                user_display="No, I'll re-enter it",
            )
            data.pop("_pending_address_lookup", None)
            _save_wizard_data(request, token, data)
            return JsonResponse({
                "ok": True,
                "done": False,
                "user_display": "No, I'll re-enter it",
                "next": {
                    "id": "street_address",
                    "avery_messages": ["I couldn't verify that address. Can you enter the full street address and ZIP?"],
                    "input": {"type": "text", "chips": [], "placeholder": "Street address", "card_type": ""},
                },
                "progress": {"index": len(completed), "total": len(turns)},
            })

        selected_index = None
        if answer.startswith("__address_select_") and answer.endswith("__"):
            try:
                selected_index = int(answer.replace("__address_select_", "").replace("__", ""))
            except ValueError:
                selected_index = None
        if selected_index is None or selected_index < 0 or selected_index >= len(suggestions):
            return JsonResponse({"ok": False, "error": "Please pick one of the address options."})

        selected = suggestions[selected_index]
        basic_info = data.setdefault("basic_info", {})
        basic_info["street_address"] = selected.get("street") or ""
        basic_info["zip_code"] = selected.get("zip_code") or ""
        basic_info["state"] = selected.get("state") or basic_info.get("state", "")
        basic_info["city"] = selected.get("city") or ""
        basic_info["formatted_address"] = selected.get("formatted") or ""

        _store_normalized_answer(
            data,
            question_key="street_address",
            raw_value=pending.get("raw_street") or selected.get("street") or "",
            normalized_value=selected.get("street") or "",
            display_value=selected.get("formatted") or selected.get("street") or "",
            confidence=float(selected.get("confidence") or 0),
            metadata={"provider": selected.get("source"), "city": selected.get("city"), "state": selected.get("state"), "zip_code": selected.get("zip_code")},
        )
        _store_normalized_answer(
            data,
            question_key="zip_code",
            raw_value=pending.get("raw_zip") or selected.get("zip_code") or "",
            normalized_value=selected.get("zip_code") or "",
            display_value=selected.get("zip_code") or "",
            confidence=float(selected.get("confidence") or 0),
            metadata={"provider": selected.get("source")},
        )
        _store_normalized_answer(
            data,
            question_key="state",
            raw_value=basic_info.get("state") or "",
            normalized_value=selected.get("state") or "",
            display_value=selected.get("state") or "",
            confidence=float(selected.get("confidence") or 0),
            metadata={"provider": selected.get("source")},
        )

        _append_chat_exchange(
            data,
            avery_messages=_address_confirmation_turn(suggestions, status=str(pending.get("status") or "needs_confirmation"))["avery_messages"],
            user_display=selected.get("formatted") or selected.get("street") or "Address confirmed",
        )
        data.pop("_pending_address_lookup", None)
        completed.add("street_address")
        completed.add("zip_code")
        completed.add("state")
        data["_completed_turns"] = list(completed)
        _save_wizard_data(request, token, data)

        turns = build_turns(data, modules)
        completed = set(data.get("_completed_turns", []))
        next_turn = find_current_turn(turns, completed)
        if next_turn is None:
            return JsonResponse({
                "ok": True,
                "done": True,
                "user_display": selected.get("formatted") or selected.get("street") or "Address confirmed",
                "redirect_url": reverse("intake_submit", args=[token]),
            })
        return JsonResponse({
            "ok": True,
            "done": False,
            "user_display": selected.get("formatted") or selected.get("street") or "Address confirmed",
            "next": _serialize_turn(next_turn, data, link),
            "progress": {"index": len(completed), "total": len(turns)},
        })

    if turn_id == "first_name_confirm":
        pending_full_name = normalize_name(str(data.get("_pending_full_name") or ""))
        if not pending_full_name:
            return JsonResponse({"ok": False, "error": "Please enter your first name again."})

        confirmation_turn = _first_name_confirmation_turn(pending_full_name)
        if answer == "__reenter__":
            _append_chat_exchange(
                data,
                avery_messages=confirmation_turn["avery_messages"],
                user_display="Re-enter",
            )
            data.pop("_pending_full_name", None)
            _save_wizard_data(request, token, data)
            return JsonResponse({
                "ok": True,
                "done": False,
                "user_display": "Re-enter",
                "next": {
                    "id": "first_name",
                    "avery_messages": ["No problem — what should I use as your first name?"],
                    "input": {"type": "text", "chips": [], "placeholder": "Your first name", "card_type": ""},
                },
                "progress": {"index": len(completed), "total": len(turns)},
            })

        first_name, last_name = split_full_name(pending_full_name)
        basic_info = data.setdefault("basic_info", {})

        if answer == "__full_name__":
            basic_info["first_name"] = first_name
            basic_info["last_name"] = last_name
            _store_normalized_answer(data, question_key="first_name", raw_value=pending_full_name, normalized_value=first_name)
            _store_normalized_answer(data, question_key="last_name", raw_value=pending_full_name, normalized_value=last_name)
            completed.add("first_name")
            completed.add("last_name")
            user_display = "That's my full name"
        elif answer == "__just_first__":
            basic_info["first_name"] = first_name
            _store_normalized_answer(data, question_key="first_name", raw_value=pending_full_name, normalized_value=first_name)
            completed.add("first_name")
            user_display = f"Just {first_name}"
        else:
            return JsonResponse({"ok": False, "error": "Please choose one of the options."})

        _sync_primary_household_member(data)
        _append_chat_exchange(
            data,
            avery_messages=confirmation_turn["avery_messages"],
            user_display=user_display,
        )
        data.pop("_pending_full_name", None)
        data["_completed_turns"] = list(completed)
        _save_wizard_data(request, token, data)

        turns = build_turns(data, modules)
        completed = set(data.get("_completed_turns", []))
        next_turn = find_current_turn(turns, completed)
        if next_turn is None:
            return JsonResponse({
                "ok": True,
                "done": True,
                "user_display": user_display,
                "redirect_url": reverse("intake_submit", args=[token]),
            })

        return JsonResponse({
            "ok": True,
            "done": False,
            "user_display": user_display,
            "next": _serialize_turn(next_turn, data, link),
            "progress": {"index": len(completed), "total": len(turns)},
        })

    # Find the turn
    turn = next((t for t in turns if t.id == turn_id), None)
    if not turn:
        return JsonResponse({"ok": False, "error": "Unknown question."}, status=400)

    # Validate required
    if turn.required and not answer:
        return JsonResponse({
            "ok": False,
            "error": "This one's required — what's your answer?",
            "next": _serialize_turn(turn, data, link),
        })

    save_answer = answer
    user_display_override: str | None = None
    question_key = TURN_TO_QUESTION_KEY.get(turn_id)

    chip_values: set[str] = set()
    for chip in turn.chips or []:
        if isinstance(chip, dict):
            chip_values.add(str(chip.get("value") or "").strip().lower())
        else:
            chip_values.add(str(chip or "").strip().lower())
    is_yes_no_turn = bool(chip_values) and chip_values.issubset({"yes", "no"})
    if is_yes_no_turn and answer:
        normalized_bool = normalize_yes_no(answer)
        if not normalized_bool.ok:
            return JsonResponse({"ok": False, "error": normalized_bool.error, "next": _serialize_turn(turn, data, link)})
        save_answer = normalized_bool.normalized or answer
        user_display_override = normalized_bool.display or save_answer

    if turn_id == "first_name" and answer:
        normalized_first_name = normalize_name(answer)
        if detect_possible_full_name(normalized_first_name):
            _append_chat_exchange(
                data,
                avery_messages=_evaluate_turn_messages(turn, data),
                user_display=normalized_first_name,
            )
            data["_pending_full_name"] = normalized_first_name
            _save_wizard_data(request, token, data)
            return JsonResponse({
                "ok": True,
                "done": False,
                "user_display": normalized_first_name,
                "next": _first_name_confirmation_turn(normalized_first_name),
                "progress": {"index": len(completed), "total": len(turns)},
            })
        save_answer = normalized_first_name
        user_display_override = normalized_first_name
        _store_normalized_answer(
            data,
            question_key="first_name",
            raw_value=answer,
            normalized_value=normalized_first_name,
        )

    if turn_id == "last_name" and answer:
        normalized_last_name = normalize_name(answer)
        save_answer = normalized_last_name
        user_display_override = normalized_last_name
        _store_normalized_answer(
            data,
            question_key="last_name",
            raw_value=answer,
            normalized_value=normalized_last_name,
        )

    if turn_id == "dob" and answer:
        normalized_dob = normalize_date(answer)
        if not normalized_dob.ok:
            return JsonResponse({"ok": False, "error": normalized_dob.error, "next": _serialize_turn(turn, data, link)})
        save_answer = normalized_dob.normalized or answer
        user_display_override = normalized_dob.display or save_answer
        _store_normalized_answer(
            data,
            question_key="primary_date_of_birth",
            raw_value=answer,
            normalized_value=save_answer,
            display_value=normalized_dob.display or save_answer,
        )

    if turn_id == "phone" and answer and answer != "__skip__":
        normalized_phone = normalize_phone(answer)
        if not normalized_phone.ok:
            return JsonResponse({"ok": False, "error": normalized_phone.error, "next": _serialize_turn(turn, data, link)})
        save_answer = normalized_phone.normalized or answer
        user_display_override = normalized_phone.display or save_answer
        _store_normalized_answer(
            data,
            question_key="phone",
            raw_value=answer,
            normalized_value=save_answer,
            display_value=normalized_phone.display or save_answer,
        )

    if turn_id == "email" and answer and answer != "__skip__":
        normalized_email = normalize_email(answer)
        if not normalized_email.ok:
            return JsonResponse({"ok": False, "error": normalized_email.error, "next": _serialize_turn(turn, data, link)})
        save_answer = normalized_email.normalized or ""
        user_display_override = normalized_email.display or ""
        _store_normalized_answer(
            data,
            question_key="email",
            raw_value=answer,
            normalized_value=save_answer,
            display_value=user_display_override,
        )

    if turn_id == "state" and answer and answer != "__skip__":
        normalized_state = normalize_state(answer)
        if not normalized_state.ok:
            return JsonResponse({"ok": False, "error": normalized_state.error, "next": _serialize_turn(turn, data, link)})
        save_answer = normalized_state.normalized or answer
        user_display_override = normalized_state.display or save_answer
        _store_normalized_answer(
            data,
            question_key="state",
            raw_value=answer,
            normalized_value=save_answer,
            display_value=user_display_override,
        )

    if turn_id == "zip_code" and answer and answer != "__skip__":
        normalized_zip = normalize_zip(answer)
        if not normalized_zip.ok:
            return JsonResponse({"ok": False, "error": normalized_zip.error, "next": _serialize_turn(turn, data, link)})
        save_answer = normalized_zip.normalized or answer
        user_display_override = normalized_zip.display or save_answer
        _store_normalized_answer(
            data,
            question_key="zip_code",
            raw_value=answer,
            normalized_value=save_answer,
            display_value=user_display_override,
        )

    if turn_id == "street_address" and answer and answer != "__skip__":
        cleaned_street = normalize_address_input(answer)
        save_answer = cleaned_street
        user_display_override = cleaned_street
        _store_normalized_answer(
            data,
            question_key="street_address",
            raw_value=answer,
            normalized_value=cleaned_street,
            display_value=cleaned_street,
            validation_status="pending_confirmation",
        )

    if turn_id == "health_income" and answer and answer != "__skip__":
        normalized_income = normalize_income(answer)
        if not normalized_income.ok:
            return JsonResponse({"ok": False, "error": normalized_income.error, "next": _serialize_turn(turn, data, link)})
        save_answer = normalized_income.normalized or answer
        user_display_override = normalized_income.display or save_answer
        _store_normalized_answer(
            data,
            question_key="estimated_household_income",
            raw_value=answer,
            normalized_value=save_answer,
            display_value=user_display_override,
        )

    if turn_id == "auto_liability" and answer:
        normalized_liability = normalize_liability_limit(answer)
        if not normalized_liability.ok:
            return JsonResponse({"ok": False, "error": normalized_liability.error, "next": _serialize_turn(turn, data, link)})
        save_answer = normalized_liability.normalized or answer
        user_display_override = normalized_liability.display or save_answer
        _store_normalized_answer(
            data,
            question_key="auto_liability_limit",
            raw_value=answer,
            normalized_value=save_answer,
            display_value=user_display_override,
        )

    if question_key and question_key not in {"first_name", "last_name", "primary_date_of_birth", "phone"} and answer and answer != "__skip__":
        _store_normalized_answer(data, question_key=question_key, raw_value=answer, normalized_value=save_answer)

    # Run save function
    if turn.save and save_answer:
        error = turn.save(save_answer, data)
        if error:
            return JsonResponse({"ok": False, "error": error, "next": _serialize_turn(turn, data, link)})

    if turn_id == "street_address" and save_answer and save_answer != "__skip__":
        basic_info = data.setdefault("basic_info", {})
        pending = data.setdefault("_pending_address_lookup", {})
        pending["raw_street"] = answer
        pending["street"] = str(basic_info.get("street_address") or save_answer or "")

    if turn_id in {"zip_code", "state", "street_address"} and save_answer != "__skip__":
        basic_info = data.setdefault("basic_info", {})
        street_value = str(basic_info.get("street_address") or "").strip()
        zip_value = str(basic_info.get("zip_code") or "").strip()
        state_value = str(basic_info.get("state") or "").strip()
        if turn_id == "street_address" and not zip_value:
            pass
        elif street_value and zip_value:
            lookup_result = _run_address_lookup(street_address=street_value, zip_code=zip_value, state=state_value)
            status = lookup_result.get("status", "no_match")
            suggestions = list(lookup_result.get("suggestions") or [])
            if status == "no_match":
                data["_pending_address_lookup"] = {
                    "status": "no_match",
                    "raw_street": answer if turn_id == "street_address" else street_value,
                    "raw_zip": zip_value,
                    "suggestions": [],
                }
                _save_wizard_data(request, token, data)
                return JsonResponse({
                    "ok": False,
                    "error": "I couldn't verify that address. Can you enter the full street address and ZIP?",
                    "next": {
                        "id": "street_address",
                        "avery_messages": ["I couldn't verify that address. Can you enter the full street address and ZIP?"],
                        "input": {"type": "text", "chips": [], "placeholder": "Street address", "card_type": ""},
                    },
                })

            if suggestions:
                data["_pending_address_lookup"] = {
                    "status": status,
                    "raw_street": answer if turn_id == "street_address" else street_value,
                    "raw_zip": zip_value,
                    "normalized_street": lookup_result.get("normalized_street") or street_value,
                    "suggestions": suggestions,
                }
                _append_chat_exchange(
                    data,
                    avery_messages=_evaluate_turn_messages(turn, data),
                    user_display=user_display_override or _get_user_display(turn, save_answer),
                )
                completed.add(turn_id)
                data["_completed_turns"] = list(completed)
                _save_wizard_data(request, token, data)
                return JsonResponse({
                    "ok": True,
                    "done": False,
                    "user_display": user_display_override or _get_user_display(turn, save_answer),
                    "next": _address_confirmation_turn(suggestions, status=status),
                    "progress": {"index": len(completed), "total": len(turns)},
                })

    # Append to chat history
    user_display = user_display_override or _get_user_display(turn, save_answer)
    _append_chat_exchange(
        data,
        avery_messages=_evaluate_turn_messages(turn, data),
        user_display=user_display,
    )

    # Mark turn complete
    completed.add(turn_id)
    data.pop("_pending_full_name", None)
    data["_completed_turns"] = list(completed)
    _save_wizard_data(request, token, data)

    # Rebuild turns (may change after save)
    turns = build_turns(data, modules)
    completed = set(data.get("_completed_turns", []))
    next_turn = find_current_turn(turns, completed)

    if next_turn is None:
        # All done
        return JsonResponse({
            "ok": True,
            "done": True,
            "user_display": user_display,
            "redirect_url": reverse("intake_submit", args=[token]),
        })

    return JsonResponse({
        "ok": True,
        "done": False,
        "user_display": user_display,
        "next": _serialize_turn(next_turn, data, link),
        "progress": {"index": len(completed), "total": len(turns)},
    })


def _serialize_turn(turn, data: dict, link) -> dict:
    """Convert a Turn to JSON-serializable dict."""
    if turn is None:
        return {}

    # Evaluate callable messages
    messages = []
    for msg in turn.avery_messages:
        if callable(msg):
            messages.append(msg(data))
        else:
            messages.append(msg)

    input_config = {
        "type": turn.input_type,
        "chips": turn.chips,
        "placeholder": turn.placeholder,
        "card_type": turn.card_type,
    }

    # For inline_card turns, render HTML
    if turn.input_type == "inline_card":
        if turn.card_type == "consent":
            input_config["card_html"] = _render_consent_card(data, link)
        elif turn.card_type == "household_members":
            input_config["card_html"] = _render_household_form(data, link)
        elif turn.card_type == "prescription":
            temp_id = turn.id.removeprefix("prescription_")
            input_config["card_html"] = _render_prescription_card(data, link, temp_id)

    return {
        "id": turn.id,
        "avery_messages": messages,
        "input": input_config,
    }


def _get_user_display(turn, answer: str) -> str:
    """Convert raw answer to display text for user bubble."""
    if answer == "__skip__" or answer == "__auto__" or answer == "__household_done__" or answer == "__prescription_done__":
        return ""

    # For chips, look up the label
    if turn.chips and answer:
        for chip in turn.chips:
            if isinstance(chip, dict) and chip.get("value") == answer:
                return chip.get("label", answer)
            elif isinstance(chip, str) and chip == answer:
                return chip

    return answer


def _render_consent_card(data: dict, link) -> str:
    """Render the consent form as HTML."""
    token = link.token
    return f"""
<div class="card card-pad">
  <h4 style="font-size:13px;font-weight:600;margin-bottom:12px;">Consent</h4>
  <form method="post" action="{reverse('intake_submit', args=[token])}" class="consent-form">
    <input type="hidden" name="csrfmiddlewaretoken" />
    <label style="display:flex;gap:8px;align-items:flex-start;margin-bottom:12px;">
      <input type="checkbox" name="consent_terms" required />
      <span style="flex:1;font-size:14px;line-height:1.4;">I agree to the terms of service</span>
    </label>
    <label style="display:flex;gap:8px;align-items:flex-start;margin-bottom:12px;">
      <input type="checkbox" name="consent_privacy" required />
      <span style="flex:1;font-size:14px;line-height:1.4;">I acknowledge the privacy policy</span>
    </label>
    <label style="display:flex;gap:8px;align-items:flex-start;margin-bottom:12px;">
      <input type="checkbox" name="consent_contact" required />
      <span style="flex:1;font-size:14px;line-height:1.4;">I consent to be contacted about my application</span>
    </label>
    <label style="display:flex;gap:8px;align-items:flex-start;">
      <input type="checkbox" name="consent_referral_sharing" required />
      <span style="flex:1;font-size:14px;line-height:1.4;">I consent to information sharing with partner agents</span>
    </label>
  </form>
</div>
"""


def _render_household_form(data: dict, link) -> str:
    """Render the household member management form as HTML."""
    basic_info = data.get("basic_info", {})
    members = data.get("household_members", [])
    household_type = data.get("_household_type", "solo")
    token = link.token

    # Primary member info
    primary_name = f"{basic_info.get('first_name', '')} {basic_info.get('last_name', '')}".strip()
    primary_dob = basic_info.get("primary_date_of_birth", "")

    # Filter spouse and dependents
    spouse = next((m for m in members if m.get("role") == "spouse"), None)
    dependents = [m for m in members if m.get("role") == "dependent"]

    html = f"""
<div class="card card-pad" id="household-form-card">
  <h4 style="font-size:13px;font-weight:600;margin-bottom:16px;">Household Members</h4>

  <!-- Primary member (always shown) -->
  <div style="padding:12px;background:#f9f9f9;border-radius:8px;margin-bottom:16px;">
    <div style="font-weight:500;color:#333;margin-bottom:8px;">You</div>
    <div style="font-size:13px;color:#666;">
      <div>{primary_name or "(name not filled)"}</div>
      <div>{primary_dob or "(DOB not filled)"}</div>
    </div>
  </div>

  <!-- Spouse section (if applicable) -->
  """

    if household_type in ("spouse", "spouse_and_dependents"):
        html += f"""
  <div style="margin-bottom:16px;">
    <div style="font-weight:500;color:#333;margin-bottom:8px;">Spouse</div>
    """
        if spouse:
            spouse_name = f"{spouse.get('first_name', '')} {spouse.get('last_name', '')}".strip()
            spouse_dob = spouse.get("date_of_birth", "")
            html += f"""
    <div style="padding:12px;background:#f9f9f9;border-radius:8px;margin-bottom:8px;">
      <div style="font-size:13px;color:#666;">
        <div>{spouse_name}</div>
        <div>{spouse_dob}</div>
      </div>
      <button type="button" class="household-remove-btn" data-role="spouse" style="font-size:11px;color:#d9534f;cursor:pointer;margin-top:8px;">Remove spouse</button>
    </div>
    """
        else:
            html += f"""
    <form class="household-add-form" data-role="spouse" style="padding:12px;background:#f9f9f9;border-radius:8px;">
      <input type="hidden" name="role" value="spouse" />
      <input type="text" name="first_name" placeholder="First name" style="width:100%;padding:8px;margin-bottom:8px;border:1px solid #ddd;border-radius:4px;" required />
      <input type="text" name="last_name" placeholder="Last name" style="width:100%;padding:8px;margin-bottom:8px;border:1px solid #ddd;border-radius:4px;" />
      <input type="date" name="date_of_birth" placeholder="DOB" style="width:100%;padding:8px;margin-bottom:8px;border:1px solid #ddd;border-radius:4px;" required />
      <button type="submit" class="btn brand sm" style="width:100%;">Add spouse</button>
    </form>
    """
        html += "</div>"

    # Dependents section (if applicable)
    if household_type in ("dependents", "spouse_and_dependents"):
        html += f"""
  <div>
    <div style="font-weight:500;color:#333;margin-bottom:8px;">Dependents</div>
    """
        if dependents:
            for dep in dependents:
                dep_name = f"{dep.get('first_name', '')} {dep.get('last_name', '')}".strip()
                dep_dob = dep.get("date_of_birth", "")
                dep_id = dep.get("temp_id", "")
                html += f"""
    <div style="padding:12px;background:#f9f9f9;border-radius:8px;margin-bottom:8px;">
      <div style="font-size:13px;color:#666;">
        <div>{dep_name}</div>
        <div>{dep_dob}</div>
      </div>
      <button type="button" class="household-remove-btn" data-temp-id="{dep_id}" data-role="dependent" style="font-size:11px;color:#d9534f;cursor:pointer;margin-top:8px;">Remove</button>
    </div>
    """

        html += f"""
    <form class="household-add-form" data-role="dependent" style="padding:12px;background:#f0f0f0;border-radius:8px;border:2px dashed #ccc;margin-bottom:8px;">
      <input type="hidden" name="role" value="dependent" />
      <input type="text" name="first_name" placeholder="First name" style="width:100%;padding:8px;margin-bottom:8px;border:1px solid #ddd;border-radius:4px;" required />
      <input type="text" name="last_name" placeholder="Last name" style="width:100%;padding:8px;margin-bottom:8px;border:1px solid #ddd;border-radius:4px;" />
      <input type="date" name="date_of_birth" placeholder="DOB" style="width:100%;padding:8px;margin-bottom:8px;border:1px solid #ddd;border-radius:4px;" required />
      <button type="submit" class="btn brand sm" style="width:100%;">Add dependent</button>
    </form>
    </div>
    """

    html += """
  <button type="button" class="household-done-btn btn brand lg full" style="margin-top:16px;">Done adding members</button>
</div>
"""
    return html


def _handle_household_member_add(request: HttpRequest, token: str, data: dict, link, role: str, first_name: str, last_name: str, dob: str) -> JsonResponse:
    """Handle adding a household member."""
    from apps.intake.conversation import _upsert_household_member
    from dateutil.parser import parse as parse_date
    from dateutil.parser import ParserError

    try:
        dt = parse_date(dob, dayfirst=False)
        dob_iso = dt.date().isoformat()
    except (ParserError, ValueError):
        return JsonResponse({
            "ok": False,
            "error": "I couldn't read that date — try MM/DD/YYYY, like 04/05/1967.",
            "card_html": _render_household_form(data, link),
        })

    _upsert_household_member(data, role, first_name, last_name, dob_iso)
    _save_wizard_data(request, token, data)

    return JsonResponse({
        "ok": True,
        "card_html": _render_household_form(data, link),
    })


def _handle_household_member_remove(request: HttpRequest, token: str, data: dict, link, role: str, temp_id: str) -> JsonResponse:
    """Handle removing a household member."""
    members = data.get("household_members", [])
    if role == "spouse":
        data["household_members"] = [m for m in members if m.get("role") != "spouse"]
    else:
        data["household_members"] = [m for m in members if m.get("temp_id") != temp_id]

    _save_wizard_data(request, token, data)

    return JsonResponse({
        "ok": True,
        "card_html": _render_household_form(data, link),
    })


def _render_prescription_card(data: dict, link, temp_id: str) -> str:
    """Render prescription card for a household member."""
    medications = _get_prescriptions_for_member(data, temp_id)

    # Get member name
    if temp_id == "primary":
        name = data.get("basic_info", {}).get("first_name", "You")
    else:
        member = next((m for m in data.get("household_members", []) if m.get("temp_id") == temp_id), None)
        name = member.get("first_name", "This person") if member else "This person"

    search_url = reverse("drug_search", args=[])

    html = f'<div id="prescription-card-{temp_id}" style="padding:16px;">'
    html += f'<h3 style="margin:0 0 16px; font-size:15px;"><strong>{name}</strong></h3>'

    # List of medications
    if medications:
        html += '<div style="margin-bottom:16px;">'
        for i, med in enumerate(medications):
            html += f'''
            <div style="display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid var(--line);">
              <span style="font-size:14px;">{med.get("drug_name", "Unknown")}</span>
              <button type="button" class="prescription-remove-btn btn ghost sm" data-temp-id="{temp_id}" data-drug-index="{i}">Remove</button>
            </div>
            '''
        html += '</div>'

    # Drug search widget
    html += f'''
    <div class="drug-search-root" data-search-url="{search_url}">
      <input type="text" name="drug_search" placeholder="Search medication..." style="width:100%; padding:8px; border:1px solid var(--line-2); border-radius:6px; font-size:14px; margin-bottom:8px;" />
      <div data-search-results style="display:flex; flex-direction:column; gap:4px; max-height:200px; overflow-y:auto;"></div>
      <input type="hidden" name="selected_drug_id" />
      <input type="hidden" name="selected_drug_name" />
      <input type="hidden" name="normalized_drug_name" />
      <input type="hidden" name="source" />
    </div>

    <button type="button" class="prescription-add-medication-btn btn outline sm" style="width:100%; margin-top:12px;">Add medication</button>

    <button type="button" class="prescription-done-btn btn brand lg full" style="margin-top:16px;">Done adding medications</button>
    </div>
    '''

    return html


def _handle_prescription_add(request: HttpRequest, token: str, data: dict, link, body: dict) -> JsonResponse:
    """Handle adding a medication to a member."""
    temp_id = body.get("temp_id", "")
    drug_name = body.get("drug_name", "").strip()
    drug_id = body.get("drug_id", "")
    normalized_name = body.get("normalized_name", "")
    source = body.get("source", "")

    if not drug_name:
        return JsonResponse({
            "ok": False,
            "error": "Please search for and select a medication.",
        })

    medications = _get_prescriptions_for_member(data, temp_id)
    medications.append({
        "drug_name": drug_name,
        "drug_id": drug_id,
        "normalized_name": normalized_name,
        "source": source,
    })
    _set_prescriptions_for_member(data, temp_id, medications)
    _save_wizard_data(request, token, data)

    return JsonResponse({
        "ok": True,
        "card_html": _render_prescription_card(data, link, temp_id),
    })


def _handle_prescription_remove(request: HttpRequest, token: str, data: dict, link, body: dict) -> JsonResponse:
    """Handle removing a medication from a member."""
    temp_id = body.get("temp_id", "")
    drug_index = int(body.get("drug_index", -1))

    if drug_index < 0:
        return JsonResponse({
            "ok": False,
            "error": "Invalid medication index.",
        })

    medications = _get_prescriptions_for_member(data, temp_id)
    if 0 <= drug_index < len(medications):
        medications.pop(drug_index)

    _set_prescriptions_for_member(data, temp_id, medications)
    _save_wizard_data(request, token, data)

    return JsonResponse({
        "ok": True,
        "card_html": _render_prescription_card(data, link, temp_id),
    })
