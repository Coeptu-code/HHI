from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Question:
    key: str
    text: str
    field_type: str = "text"
    choices: tuple[tuple[str, str], ...] = ()
    required: bool = True
    helper_text: str = ""
    supports: tuple[str, ...] = ()
    include_when_modules: tuple[str, ...] = ()
    position: int = 100
    condition_key: str | None = None
    condition_value: str | bool | None = None


STEP_LABELS = {
    "basic": "Basic Info",
    "household": "Household",
    "health": "Health Coverage",
    "household_coverage": "Household Coverage Needs",
    "prescription_check": "Prescription Check",
    "life": "Protection Planning",
    "auto": "Vehicle Coverage",
    "home": "Property Coverage",
    "umbrella": "Extra Liability Protection",
    "consent": "Consent",
}


STEP_ORDER = (
    "basic",
    "household",
    "health",
    "household_coverage",
    "prescription_check",
    "life",
    "auto",
    "home",
    "umbrella",
    "consent",
)

MODULE_STEP_MAP = {
    "health": "health",
    "life": "life",
    "auto": "auto",
    "home": "home",
    "umbrella": "umbrella",
}


QUESTION_BANK: tuple[Question, ...] = (
    Question(
        key="first_name",
        text="First name",
        supports=("basic",),
        position=10,
    ),
    Question(
        key="last_name",
        text="Last name",
        supports=("basic",),
        position=20,
    ),
    Question(
        key="email",
        text="Email",
        field_type="email",
        required=False,
        helper_text="Optional, but recommended for follow-up.",
        supports=("basic",),
        position=30,
    ),
    Question(
        key="phone",
        text="Phone",
        field_type="phone",
        required=False,
        helper_text="Optional, but recommended for follow-up.",
        supports=("basic",),
        position=40,
    ),
    Question(
        key="street_address",
        text="Street address",
        required=False,
        supports=("basic",),
        position=45,
    ),
    Question(
        key="zip_code",
        text="ZIP code",
        required=False,
        supports=("basic",),
        position=48,
    ),
    Question(
        key="state",
        text="State",
        required=False,
        supports=("basic",),
        position=50,
    ),
    Question(
        key="preferred_contact_method",
        text="Preferred contact method",
        field_type="select",
        required=False,
        choices=(("phone", "Phone"), ("email", "Email"), ("text", "Text")),
        supports=("basic",),
        position=60,
    ),
    Question(
        key="main_concern",
        text="What is your main concern or goal for this call?",
        required=False,
        helper_text="Example: new coverage, switching plans, costs, prescriptions, doctors, etc.",
        supports=("basic",),
        position=70,
    ),
    Question(
        key="primary_date_of_birth",
        text="Primary applicant date of birth",
        field_type="date",
        supports=("basic", "household"),
        position=80,
    ),
    Question(
        key="current_health_coverage",
        text="Do you currently have health insurance coverage?",
        field_type="select",
        required=False,
        supports=("health",),
        include_when_modules=("health",),
        choices=(
            ("none", "No current coverage"),
            ("employer", "Employer plan"),
            ("marketplace", "Marketplace / ACA plan"),
            ("medicare", "Medicare"),
            ("medicaid", "Medicaid"),
            ("other", "Other"),
        ),
        position=210,
    ),
    Question(
        key="has_preferred_doctors",
        text="Do you have preferred doctors or facilities you want to keep in-network?",
        field_type="bool",
        required=False,
        supports=("health",),
        include_when_modules=("health",),
        position=220,
    ),
    Question(
        key="want_marketplace_help",
        text="Would you like help with Marketplace / ACA coverage options?",
        field_type="bool",
        required=False,
        supports=("health",),
        include_when_modules=("health",),
        position=230,
    ),
    Question(
        key="want_medicare_help",
        text="Would you like help with Medicare coverage options?",
        field_type="bool",
        required=False,
        supports=("health",),
        include_when_modules=("health",),
        position=240,
    ),
    Question(
        key="estimated_household_income",
        text="Estimated household income",
        field_type="number",
        required=False,
        helper_text="Rough annual estimate is fine.",
        supports=("health",),
        include_when_modules=("health",),
        position=250,
    ),
    Question(
        key="anyone_depends_on_income_or_care",
        text="Does anyone depend on your income or care?",
        field_type="bool",
        required=False,
        supports=("life",),
        include_when_modules=("life",),
        position=310,
    ),
    Question(
        key="has_life_insurance",
        text="Do you currently have life insurance?",
        field_type="bool",
        required=False,
        supports=("life",),
        include_when_modules=("life",),
        position=320,
    ),
    Question(
        key="has_mortgage_or_major_debt",
        text="Do you have a mortgage or major debt that would be hard to cover without your income?",
        field_type="bool",
        required=False,
        supports=("life",),
        include_when_modules=("life",),
        position=330,
    ),
    Question(
        key="income_would_be_hard_to_replace",
        text="Would your household struggle to replace your income if something happened to you?",
        field_type="bool",
        required=False,
        supports=("life",),
        include_when_modules=("life",),
        position=340,
    ),
    Question(
        key="wants_life_referral",
        text="Would you like to be connected with a licensed partner agent to discuss life coverage?",
        field_type="bool",
        required=False,
        supports=("life",),
        include_when_modules=("life",),
        position=350,
    ),
    Question(
        key="owns_or_drives_vehicle",
        text="Do you own or regularly drive a vehicle?",
        field_type="bool",
        required=False,
        supports=("auto",),
        include_when_modules=("auto",),
        position=410,
    ),
    Question(
        key="has_auto_insurance",
        text="Do you currently have auto insurance?",
        field_type="bool",
        required=False,
        supports=("auto",),
        include_when_modules=("auto",),
        position=420,
    ),
    Question(
        key="auto_liability_limit",
        text="How would you describe your auto bodily injury liability limits?",
        field_type="select",
        required=False,
        supports=("auto",),
        include_when_modules=("auto",),
        choices=(
            ("unknown", "Not sure"),
            ("state_minimum", "State minimum"),
            ("low", "Low"),
            ("standard", "Standard"),
            ("high", "High"),
        ),
        position=430,
    ),
    Question(
        key="teen_driver_in_household",
        text="Is there a teen driver in the household?",
        field_type="bool",
        required=False,
        supports=("auto",),
        include_when_modules=("auto",),
        position=440,
    ),
    Question(
        key="wants_auto_referral",
        text="Would you like to be connected with a licensed partner agent to review auto coverage?",
        field_type="bool",
        required=False,
        supports=("auto",),
        include_when_modules=("auto",),
        position=450,
    ),
    Question(
        key="owns_home",
        text="Do you own a home?",
        field_type="bool",
        required=False,
        supports=("home",),
        include_when_modules=("home",),
        position=510,
    ),
    Question(
        key="has_home_insurance",
        text="Do you currently have homeowners insurance?",
        field_type="bool",
        required=False,
        supports=("home",),
        include_when_modules=("home",),
        position=520,
    ),
    Question(
        key="owns_rental_property",
        text="Do you own rental property?",
        field_type="bool",
        required=False,
        supports=("home", "umbrella"),
        include_when_modules=("home",),
        position=530,
    ),
    Question(
        key="wants_home_referral",
        text="Would you like to be connected with a licensed partner agent to review home coverage?",
        field_type="bool",
        required=False,
        supports=("home",),
        include_when_modules=("home",),
        position=540,
    ),
    Question(
        key="has_umbrella",
        text="Do you currently have umbrella coverage?",
        field_type="bool",
        required=False,
        supports=("umbrella",),
        include_when_modules=("umbrella",),
        position=610,
    ),
    Question(
        key="assets_over_250k",
        text="Are your total assets approximately over $250,000?",
        field_type="bool",
        required=False,
        supports=("umbrella",),
        include_when_modules=("umbrella",),
        position=620,
    ),
    Question(
        key="has_extra_liability_risk",
        text="Do you have extra liability risk (pool, trampoline, boat, ATV, or high-risk hobbies)?",
        field_type="bool",
        required=False,
        supports=("umbrella",),
        include_when_modules=("umbrella",),
        position=630,
    ),
    Question(
        key="wants_umbrella_referral",
        text="Would you like to be connected with a licensed partner agent to review umbrella coverage?",
        field_type="bool",
        required=False,
        supports=("umbrella",),
        include_when_modules=("umbrella",),
        position=640,
    ),
)


CONSENT_FIELDS = (
    "consent_terms",
    "consent_privacy",
    "consent_contact",
    "consent_referral_sharing",
)


def get_visible_steps(selected_modules: Iterable[str]) -> list[str]:
    ordered_modules: list[str] = []
    for module in selected_modules:
        normalized = module.strip().lower() if module else ""
        if normalized not in MODULE_STEP_MAP:
            continue
        if normalized in ordered_modules:
            continue
        ordered_modules.append(normalized)

    steps = ["basic", "household"]
    for module in ordered_modules:
        if module == "health":
            steps.extend(["health", "household_coverage", "prescription_check"])
        else:
            steps.append(MODULE_STEP_MAP[module])
    steps.append("consent")
    return steps


def get_step_questions(step: str, selected_modules: Iterable[str]) -> tuple[Question, ...]:
    if step not in STEP_ORDER:
        return ()

    selected = {module.strip().lower() for module in selected_modules if module and module.strip()}
    questions: list[Question] = []
    for question in QUESTION_BANK:
        if step not in question.supports:
            continue
        if question.include_when_modules and not selected.intersection(question.include_when_modules):
            continue
        questions.append(question)
    questions.sort(key=lambda item: item.position)
    return tuple(questions)


def get_question_by_key(key: str) -> Question | None:
    for question in QUESTION_BANK:
        if question.key == key:
            return question
    return None
