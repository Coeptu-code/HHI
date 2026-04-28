from __future__ import annotations

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
from apps.gap_scoring.models import GapFinding
from apps.gap_scoring.services import build_coveragap_score, score_and_persist
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
from apps.questionnaires.models import QuestionnaireLink
from apps.referrals.models import ReferralOpportunity


HOUSEHOLD_HELPERS = [
    "Do not include a baby as a dependent until the baby is born.",
    "Tobacco user means used tobacco products 4 or more times per week on average during the past 6 months, not including ceremonial uses.",
    "Other coverage access means eligible for health coverage through a job, Medicare, Medicaid, or CHIP.",
]

RXTERMS_SEARCH_URL = "https://clinicaltables.nlm.nih.gov/api/rxterms/v3/search"


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


def _get_active_link(token: str) -> QuestionnaireLink:
    link = get_object_or_404(QuestionnaireLink, token=token)
    if not link.can_use():
        raise Http404("This intake link is no longer active.")
    return link


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
    data = _get_wizard_data(request, token)
    _sync_primary_household_member(data)
    _save_wizard_data(request, token, data)
    first_step = _get_visible_steps_for_data(link, data)[0]
    return render(
        request,
        "intake/welcome.html",
        {
            "link": link,
            "start_url": reverse("intake_step", args=[token, first_step]),
        },
    )


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
    customer.save()

    submission = IntakeSubmission.objects.create(
        questionnaire_link=link,
        agent=link.agent,
        customer=customer,
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
            role=member.get("role", "dependent"),
            first_name=member.get("first_name", ""),
            last_name=member.get("last_name", ""),
            date_of_birth=member["date_of_birth"],
            needs_coverage=bool(member.get("needs_coverage")),
            other_coverage_access=bool(member.get("other_coverage_access")),
            legal_parent_guardian_under_19=bool(member.get("legal_parent_guardian_under_19")),
            claimed_tax_dependent=bool(member.get("claimed_tax_dependent")),
            pregnant=bool(member.get("pregnant")),
            tobacco_user=bool(member.get("tobacco_user")),
            takes_prescriptions=bool(member.get("takes_prescriptions")),
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
    for step_name in _get_visible_steps_for_data(link, data):
        if step_name in {"household", "household_coverage", "prescription_check", "consent"} or step_name.startswith("prescription_"):
            continue
        for question in get_step_questions(step_name, link.selected_modules()):
            value = answer_map.get(question.key, "")
            IntakeAnswer.objects.create(
                submission=submission,
                module=(question.supports[0] if question.supports else ""),
                supports=",".join(question.supports),
                question_key=question.key,
                question_text=question.text,
                answer_value=_stringify_answer(value),
            )

    submission.status = "submitted"
    submission.submitted_at = timezone.now()
    submission.save(update_fields=["status", "submitted_at", "updated_at"])

    link.completed_at = timezone.now()
    link.is_active = False
    link.save(update_fields=["completed_at", "is_active"])

    score_and_persist(submission, answer_map)
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
