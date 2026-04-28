from __future__ import annotations

from typing import Any, Iterable

from django import forms
from django.core.validators import RegexValidator

from apps.intake.questions import Question


PHONE_VALIDATOR = RegexValidator(
    regex=r"^[0-9()+\-\s.]{7,}$",
    message="Enter a valid phone number.",
)

BOOL_CHOICES = (("yes", "Yes"), ("no", "No"))


class DynamicQuestionForm(forms.Form):
    def __init__(self, questions: Iterable[Question], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self._questions = tuple(questions)
        for question in self._questions:
            self.fields[question.key] = self._field_for_question(question)

    @property
    def questions(self) -> tuple[Question, ...]:
        return self._questions

    def _field_for_question(self, question: Question) -> forms.Field:
        common: dict[str, Any] = {
            "label": question.text,
            "required": question.required,
            "help_text": question.helper_text,
        }
        if question.field_type == "email":
            return forms.EmailField(**common)
        if question.field_type == "phone":
            return forms.CharField(validators=[PHONE_VALIDATOR], **common)
        if question.field_type == "date":
            return forms.DateField(
                **common,
                widget=forms.DateInput(attrs={"type": "date"}),
                input_formats=["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"],
            )
        if question.field_type == "bool":
            return forms.ChoiceField(choices=BOOL_CHOICES, widget=forms.RadioSelect, **common)
        if question.field_type == "select":
            return forms.ChoiceField(choices=(("", "-- Select --"),) + tuple(question.choices), **common)
        if question.field_type == "number":
            return forms.IntegerField(widget=forms.NumberInput(attrs={"inputmode": "numeric"}), **common)
        return forms.CharField(**common)


class BasicInfoForm(DynamicQuestionForm):
    pass


class StepQuestionForm(DynamicQuestionForm):
    pass


class ConsentForm(forms.Form):
    consent_terms = forms.BooleanField(
        required=True,
        label="I agree to the terms of service.",
    )
    consent_privacy = forms.BooleanField(
        required=True,
        label="I acknowledge the privacy policy.",
    )
    consent_contact = forms.BooleanField(
        required=True,
        label="I consent to be contacted about insurance options.",
    )
    consent_referral_sharing = forms.BooleanField(
        required=True,
        label=(
            "I understand Hutchins Health Insurance primarily provides health insurance guidance. "
            "I agree that my answers about other insurance needs may be used to identify potential coverage gaps "
            "and may be shared with licensed partner agents who can assist with those insurance lines."
        ),
    )


class HouseholdMemberForm(forms.Form):
    first_name = forms.CharField(label="First name")
    last_name = forms.CharField(label="Last name", required=False)
    date_of_birth = forms.DateField(
        label="Date of birth",
        widget=forms.DateInput(attrs={"type": "date"}),
        input_formats=["%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y"],
    )
    needs_coverage = forms.BooleanField(label="Needs coverage", required=False, initial=True)
    other_coverage_access = forms.BooleanField(
        label="Other coverage access",
        required=False,
        help_text="Eligible for health coverage through a job, Medicare, Medicaid, or CHIP.",
    )
    legal_parent_guardian_under_19 = forms.BooleanField(
        label="Legal parent or guardian of someone under 19",
        required=False,
    )
    claimed_tax_dependent = forms.BooleanField(
        label="Claimed as a tax dependent",
        required=False,
    )
    pregnant = forms.BooleanField(label="Pregnant", required=False)
    tobacco_user = forms.BooleanField(
        label="Tobacco user",
        required=False,
        help_text="Used tobacco products 4 or more times per week on average during the past 6 months, not including ceremonial uses.",
    )


MEMBER_RADIO_CHOICES = (("yes", "Yes"), ("no", "No"))


class HouseholdCoverageNeedsForm(forms.Form):
    def __init__(self, household_members: list[dict], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.household_members = household_members
        for member in household_members:
            temp_id = member["temp_id"]
            name = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
            self.fields[f"needs_coverage__{temp_id}"] = forms.ChoiceField(
                label=f"{name} needs coverage?",
                choices=MEMBER_RADIO_CHOICES,
                widget=forms.RadioSelect,
            )
            self.fields[f"other_coverage_access__{temp_id}"] = forms.ChoiceField(
                label=f"{name} eligible for other coverage?",
                choices=MEMBER_RADIO_CHOICES,
                widget=forms.RadioSelect,
            )
            self.fields[f"tobacco_user__{temp_id}"] = forms.ChoiceField(
                label=f"{name} tobacco user?",
                choices=MEMBER_RADIO_CHOICES,
                widget=forms.RadioSelect,
            )


class PrescriptionCheckForm(forms.Form):
    def __init__(self, household_members: list[dict], *args: Any, **kwargs: Any):
        super().__init__(*args, **kwargs)
        self.household_members = household_members
        for member in household_members:
            temp_id = member["temp_id"]
            name = f"{member.get('first_name', '')} {member.get('last_name', '')}".strip()
            self.fields[f"takes_prescriptions__{temp_id}"] = forms.ChoiceField(
                label=f"{name} takes prescriptions?",
                choices=MEMBER_RADIO_CHOICES,
                widget=forms.RadioSelect,
            )


class PrescriptionMedicationForm(forms.Form):
    drug_search = forms.CharField(
        label="Search medication",
        required=False,
        help_text="Type at least 2 characters. If search is unavailable, enter the medication manually.",
    )
    selected_drug_id = forms.CharField(widget=forms.HiddenInput(), required=False)
    selected_drug_name = forms.CharField(widget=forms.HiddenInput(), required=False)
    normalized_drug_name = forms.CharField(widget=forms.HiddenInput(), required=False)
    source = forms.CharField(widget=forms.HiddenInput(), required=False, initial="rxterms")
    dosage_strength = forms.CharField(label="Dosage / strength", required=False)
    frequency = forms.CharField(label="Frequency", required=False)

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        drug_search = (cleaned.get("drug_search") or "").strip()
        selected_drug_name = (cleaned.get("selected_drug_name") or "").strip()
        if not drug_search and not selected_drug_name:
            raise forms.ValidationError("Enter a medication name or select a search result.")
        return cleaned
