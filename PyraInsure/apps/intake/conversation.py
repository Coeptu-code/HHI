"""
Messenger-style conversation flow for intake.
Defines the sequence of questions Avery asks and how to process answers.
"""
from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from datetime import date
from dateutil.parser import parse as parse_date
from dateutil.parser import ParserError


@dataclass
class Turn:
    """Represents one conversation turn (Avery's question + user's input)."""
    id: str
    avery_messages: list = field(default_factory=list)  # list of str or callable(data) -> str
    input_type: str = "text"  # "text"|"date"|"chips"|"number"|"skip_chips"|"inline_card"|"none"
    chips: list = field(default_factory=list)  # [{"label":..,"value":..}] or ["Yes","No"]
    placeholder: str = ""
    required: bool = False
    save: callable = None  # (raw_answer, data) -> error_str or None
    condition: callable = None  # (data, modules) -> bool; skip if False
    auto_advance: bool = False  # no input; JS auto-sends after messages
    card_type: str = ""  # "consent" | "prescription" for inline_card


# ── Save functions ────────────────────────────────────────────────

def _save_text_field(session_key_tuple):
    """Generic save for text fields. Key tuple: (dict_key, field_name)."""
    def save(raw, data):
        d = data[session_key_tuple[0]]
        d[session_key_tuple[1]] = raw.strip()
        return None
    return save


def _save_dob(field_key="primary_date_of_birth"):
    """Parse date from natural text."""
    def save(raw, data):
        try:
            dt = parse_date(raw.strip(), dayfirst=False)
            data["basic_info"][field_key] = dt.date().isoformat()
            return None
        except (ParserError, ValueError):
            return "I couldn't read that date — try MM/DD/YYYY, like 04/05/1967."
    return save


def _save_bool_answer(answers_key):
    """Save a yes/no answer to the answers dict."""
    def save(raw, data):
        if raw == "__skip__":
            return None
        value = raw.lower() in ("yes", "y", "true", "1")
        data.setdefault("answers", {})[answers_key] = value
        return None
    return save


def _answer_yes(data: dict, key: str) -> bool:
    value = data.get("answers", {}).get(key)
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"yes", "y", "true", "1", "on"}


def _primary_age(data: dict) -> int | None:
    dob_raw = str(data.get("basic_info", {}).get("primary_date_of_birth") or "").strip()
    if not dob_raw:
        return None
    try:
        dob = parse_date(dob_raw, dayfirst=False).date()
    except (ParserError, ValueError):
        return None
    today = date.today()
    return today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))


def _household_has_spouse_or_dependents(data: dict) -> bool:
    household_type = str(data.get("_household_type") or "")
    if household_type in {"spouse", "dependents", "spouse_and_dependents"}:
        return True
    for member in data.get("household_members", []):
        if member.get("role") in {"spouse", "dependent"}:
            return True
    return False


def _medicare_path_dominates(data: dict) -> bool:
    age = _primary_age(data)
    if age is not None and age >= 64:
        coverage = str(data.get("answers", {}).get("current_health_coverage") or "").strip().lower()
        return coverage in {"medicare", "none", ""}
    return False


def _liability_exposure_likely(data: dict) -> bool:
    if _answer_yes(data, "assets_over_250k"):
        return True
    if _answer_yes(data, "owns_home"):
        return True
    if _answer_yes(data, "owns_rental_property"):
        return True
    if _answer_yes(data, "teen_driver_in_household"):
        return True
    if _answer_yes(data, "has_extra_liability_risk"):
        return True
    auto_limit = str(data.get("answers", {}).get("auto_liability_limit") or "").strip().lower()
    if auto_limit in {"unknown", "low", "state_minimum", "minimum"}:
        return True
    return False


def _save_household_composition(raw, data):
    """Save household type and initialize member structures."""
    if raw == "__skip__":
        data["_household_type"] = "solo"
        return None
    data["_household_type"] = raw
    # Initialize household_members if needed
    data.setdefault("household_members", [])
    return None


def _skip_if_not(condition_key, condition_value=True):
    """Skip this turn if condition_key in data is not condition_value."""
    def condition(data, modules):
        return data.get(condition_key) == condition_value
    return condition


def _skip_unless_module(*module_names):
    """Skip this turn unless at least one of these modules is selected."""
    def condition(data, modules):
        return any(m in modules for m in module_names)
    return condition


def _skip_if_household_type_is(*types):
    """Skip unless household_type is one of these."""
    def condition(data, modules):
        return data.get("_household_type") in types
    return condition


# ── Conversation steps ────────────────────────────────────────────

def build_turns(data: dict, modules: list) -> list[Turn]:
    """Build the full conversation turn list based on current state."""
    turns = []

    # Phase 0: Intro (auto-advance)
    turns.append(Turn(
        id="intro",
        avery_messages=[
            "Hey! I'm Avery, your insurance prep coach.",
            "I'll ask a few quick questions before your call.",
        ],
        input_type="none",
        auto_advance=True,
    ))

    # Phase 1: Basic info
    turns.append(Turn(
        id="first_name",
        avery_messages=["What's your first name?"],
        input_type="text",
        placeholder="Your first name",
        required=True,
        save=_save_text_field(("basic_info", "first_name")),
    ))

    turns.append(Turn(
        id="last_name",
        avery_messages=[lambda d: f"Nice to meet you, {d['basic_info'].get('first_name', '')}! And your last name?"],
        input_type="text",
        placeholder="Your last name",
        required=True,
        save=_save_text_field(("basic_info", "last_name")),
    ))

    turns.append(Turn(
        id="phone",
        avery_messages=["Best number to reach you? (totally optional)"],
        input_type="phone",
        placeholder="(555) 555-1212",
        chips=[{"label": "Skip", "value": "__skip__"}],
        save=lambda raw, data: (
            None if raw == "__skip__"
            else _save_text_field(("basic_info", "phone"))(raw, data)
        ),
    ))

    turns.append(Turn(
        id="email",
        avery_messages=["And a good email? (also optional)"],
        input_type="email",
        placeholder="your@email.com",
        chips=[{"label": "Skip", "value": "__skip__"}],
        save=lambda raw, data: (
            None if raw == "__skip__"
            else _save_text_field(("basic_info", "email"))(raw, data)
        ),
    ))

    turns.append(Turn(
        id="street_address",
        avery_messages=["What's your street address?"],
        input_type="text",
        placeholder="Street address",
        required=False,
        chips=[{"label": "Skip", "value": "__skip__"}],
        save=lambda raw, data: (
            None if raw == "__skip__"
            else _save_text_field(("basic_info", "street_address"))(raw, data)
        ),
    ))

    turns.append(Turn(
        id="zip_code",
        avery_messages=["What's your ZIP code?"],
        input_type="text",
        placeholder="5-digit ZIP",
        required=False,
        chips=[{"label": "Skip", "value": "__skip__"}],
        save=lambda raw, data: (
            None if raw == "__skip__"
            else _save_text_field(("basic_info", "zip_code"))(raw, data)
        ),
    ))

    turns.append(Turn(
        id="state",
        avery_messages=["What state do you live in?"],
        input_type="text",
        placeholder="e.g. California or CA",
        chips=[{"label": "Skip", "value": "__skip__"}],
        save=lambda raw, data: (
            None if raw == "__skip__"
            else _save_text_field(("basic_info", "state"))(raw, data)
        ),
    ))

    turns.append(Turn(
        id="preferred_contact_method",
        avery_messages=["What's the best way for us to follow up?"],
        input_type="chips",
        chips=[
            {"label": "Phone", "value": "phone"},
            {"label": "Email", "value": "email"},
            {"label": "Text", "value": "text"},
        ],
        save=lambda raw, data: data.setdefault("basic_info", {}).__setitem__("preferred_contact_method", raw) or None,
    ))

    turns.append(Turn(
        id="main_concern",
        avery_messages=["Anything specific you're hoping to get out of this call?"],
        input_type="skip_chips",
        placeholder="e.g. switching plans, cutting costs...",
        chips=[
            {"label": "Just exploring", "value": "exploring"},
            {"label": "Cutting costs", "value": "costs"},
            {"label": "Switching plans", "value": "switching"},
        ],
        save=lambda raw, data: (
            None if raw == "__skip__"
            else _save_text_field(("basic_info", "main_concern"))(raw, data)
        ),
    ))

    turns.append(Turn(
        id="dob",
        avery_messages=[lambda d: f"What's your date of birth, {d['basic_info'].get('first_name', '')}?"],
        input_type="date",
        placeholder="MM/DD/YYYY",
        required=True,
        save=_save_dob("primary_date_of_birth"),
    ))

    # Phase 2: Household
    turns.append(Turn(
        id="household_composition",
        avery_messages=["Tell me about your household — are you filing taxes by yourself, or with others?"],
        input_type="chips",
        chips=[
            {"label": "Just me", "value": "solo"},
            {"label": "Me + spouse", "value": "spouse"},
            {"label": "I have kids/dependents", "value": "dependents"},
            {"label": "Spouse + kids", "value": "spouse_and_dependents"},
        ],
        required=True,
        save=_save_household_composition,
    ))

    # Household member management form (if not solo)
    household_type = data.get("_household_type", "")
    if household_type and household_type != "solo":
        turns.append(Turn(
            id="household_members_form",
            avery_messages=["Let's add the details for your household members."],
            input_type="inline_card",
            card_type="household_members",
            required=True,
            save=lambda raw, data: None,  # Handled by household member add/remove endpoints
        ))

    normalized_modules: list[str] = []
    for module in modules:
        key = str(module or "").strip().lower()
        if key not in {"health", "life", "auto", "home", "umbrella"}:
            continue
        if key in normalized_modules:
            continue
        normalized_modules.append(key)

    for module in normalized_modules:
        if module == "health":
            turns.append(Turn(
                id="health_coverage",
                avery_messages=["What does your current health coverage look like?"],
                input_type="chips",
                chips=[
                    {"label": "No coverage", "value": "none"},
                    {"label": "Through my employer", "value": "employer"},
                    {"label": "ACA / Marketplace", "value": "marketplace"},
                    {"label": "Medicare", "value": "medicare"},
                    {"label": "Medicaid", "value": "medicaid"},
                    {"label": "Something else", "value": "other"},
                ],
                save=lambda raw, data: data.setdefault("answers", {}).__setitem__("current_health_coverage", raw) or None,
            ))

            coverage_value = str(data.get("answers", {}).get("current_health_coverage") or "").strip().lower()
            household_needs = any(bool(member.get("needs_coverage", True)) for member in data.get("household_members", []))
            if coverage_value not in {"none", ""} or household_needs:
                turns.append(Turn(
                    id="health_doctors",
                    avery_messages=["Do you have preferred doctors or facilities you want to keep in-network?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("has_preferred_doctors"),
                ))

            if not _medicare_path_dominates(data):
                turns.append(Turn(
                    id="health_marketplace",
                    avery_messages=["Would you like help with Marketplace / ACA coverage options?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("want_marketplace_help"),
                ))

            age = _primary_age(data)
            medicare_signal = age is not None and age >= 64
            medicare_signal = medicare_signal or ("medicare" in str(data.get("basic_info", {}).get("main_concern") or "").lower())
            medicare_signal = medicare_signal or coverage_value == "medicare"
            if medicare_signal:
                turns.append(Turn(
                    id="health_medicare",
                    avery_messages=["Would you like help with Medicare coverage options?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("want_medicare_help"),
                ))

            turns.append(Turn(
                id="health_income",
                avery_messages=["About what is your household income each year?"],
                input_type="currency",
                placeholder="e.g. 65000",
                save=lambda raw, data: (
                    None if raw == "__skip__"
                    else _save_text_field(("answers", "estimated_household_income"))(raw, data)
                ),
            ))

            for member in data.get("household_members", []):
                tid = member.get("temp_id")
                name = member.get("first_name", "This person")

                turns.append(Turn(
                    id=f"needs_coverage_{tid}",
                    avery_messages=[f"Does {name} need health coverage?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=lambda raw, data, tid=tid: _update_household_member_field(
                        data, tid, "needs_coverage", raw.lower() == "yes"
                    ),
                ))

                turns.append(Turn(
                    id=f"other_coverage_{tid}",
                    avery_messages=[f"Is {name} eligible for coverage through a job, Medicare, or Medicaid?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=lambda raw, data, tid=tid: _update_household_member_field(
                        data, tid, "other_coverage_access", raw.lower() == "yes"
                    ),
                ))

                turns.append(Turn(
                    id=f"tobacco_{tid}",
                    avery_messages=[f"Does {name} use tobacco products regularly?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=lambda raw, data, tid=tid: _update_household_member_field(
                        data, tid, "tobacco_user", raw.lower() == "yes"
                    ),
                ))

            turns.append(Turn(
                id="prescription_check",
                avery_messages=["Does anyone in your household take prescription medications regularly?"],
                input_type="chips",
                chips=["Yes", "For some", "No"],
                save=_save_bool_answer("takes_prescriptions"),
            ))

            takes = data.get("answers", {}).get("takes_prescriptions")
            if takes:
                all_members = _all_members_for_prescriptions(data)
                for member in all_members:
                    tid = member.get("temp_id", "primary")
                    name = member.get("first_name", "this person")
                    turns.append(Turn(
                        id=f"prescription_{tid}",
                        avery_messages=[f"Let's add {name}'s medications ? search and add each one below."],
                        input_type="inline_card",
                        card_type="prescription",
                        save=lambda raw, data: None,
                    ))
            continue

        if module == "life":
            turns.append(Turn(
                id="life_dependents",
                avery_messages=["Does anyone depend on your income or care?"],
                input_type="chips",
                chips=["Yes", "No"],
                save=_save_bool_answer("anyone_depends_on_income_or_care"),
            ))
            turns.append(Turn(
                id="life_mortgage",
                avery_messages=["Do you have a mortgage or major debt that would be hard to cover without your income?"],
                input_type="chips",
                chips=["Yes", "No"],
                save=_save_bool_answer("has_mortgage_or_major_debt"),
            ))
            turns.append(Turn(
                id="life_income_replace",
                avery_messages=["Would your household struggle to replace your income if something happened to you?"],
                input_type="chips",
                chips=["Yes", "No"],
                save=_save_bool_answer("income_would_be_hard_to_replace"),
            ))
            life_risk = (
                _household_has_spouse_or_dependents(data)
                or _answer_yes(data, "anyone_depends_on_income_or_care")
                or _answer_yes(data, "has_mortgage_or_major_debt")
                or _answer_yes(data, "income_would_be_hard_to_replace")
            )
            if life_risk:
                turns.append(Turn(
                    id="life_has_insurance",
                    avery_messages=["Do you currently have life insurance?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("has_life_insurance"),
                ))
                turns.append(Turn(
                    id="wants_life_referral",
                    avery_messages=["Would you like to be connected with a licensed partner agent to discuss life coverage?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("wants_life_referral"),
                ))
            continue

        if module == "auto":
            turns.append(Turn(
                id="auto_owns_vehicle",
                avery_messages=["Do you own or regularly drive a vehicle?"],
                input_type="chips",
                chips=["Yes", "No"],
                save=_save_bool_answer("owns_or_drives_vehicle"),
            ))
            if _answer_yes(data, "owns_or_drives_vehicle"):
                turns.append(Turn(
                    id="auto_has_insurance",
                    avery_messages=["Do you currently have auto insurance?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("has_auto_insurance"),
                ))
                turns.append(Turn(
                    id="auto_liability",
                    avery_messages=["How would you describe your auto bodily injury liability limits?"],
                    input_type="chips",
                    chips=[
                        {"label": "Not sure", "value": "unknown"},
                        {"label": "State minimum", "value": "state_minimum"},
                        {"label": "Low", "value": "low"},
                        {"label": "Standard", "value": "standard"},
                        {"label": "High", "value": "high"},
                    ],
                    save=lambda raw, data: data.setdefault("answers", {}).__setitem__("auto_liability_limit", raw) or None,
                ))
                turns.append(Turn(
                    id="auto_teen_driver",
                    avery_messages=["Is there a teen driver in the household?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("teen_driver_in_household"),
                ))
                turns.append(Turn(
                    id="wants_auto_referral",
                    avery_messages=["Would you like to be connected with a licensed partner agent to review auto coverage?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("wants_auto_referral"),
                ))
            continue

        if module == "home":
            turns.append(Turn(
                id="home_owns",
                avery_messages=["Do you own a home?"],
                input_type="chips",
                chips=["Yes", "No"],
                save=_save_bool_answer("owns_home"),
            ))
            if _answer_yes(data, "owns_home"):
                turns.append(Turn(
                    id="home_has_insurance",
                    avery_messages=["Do you currently have homeowners insurance?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("has_home_insurance"),
                ))
            if _answer_yes(data, "owns_home") or _answer_yes(data, "owns_rental_property"):
                turns.append(Turn(
                    id="home_rental",
                    avery_messages=["Do you own rental property?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("owns_rental_property"),
                ))
            turns.append(Turn(
                id="wants_home_referral",
                avery_messages=["Would you like to be connected with a licensed partner agent to review home coverage?"],
                input_type="chips",
                chips=["Yes", "No"],
                save=_save_bool_answer("wants_home_referral"),
            ))
            continue

        if module == "umbrella":
            if _liability_exposure_likely(data):
                turns.append(Turn(
                    id="umbrella_has",
                    avery_messages=["Do you currently have umbrella coverage?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("has_umbrella"),
                ))
                turns.append(Turn(
                    id="umbrella_assets",
                    avery_messages=["Are your total assets approximately over $250,000?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("assets_over_250k"),
                ))
                turns.append(Turn(
                    id="umbrella_risk",
                    avery_messages=["Do you have extra liability risk such as pool, trampoline, boat, ATV, or high-risk hobbies?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("has_extra_liability_risk"),
                ))
                turns.append(Turn(
                    id="wants_umbrella_referral",
                    avery_messages=["Would you like to be connected with a licensed partner agent to review umbrella coverage?"],
                    input_type="chips",
                    chips=["Yes", "No"],
                    save=_save_bool_answer("wants_umbrella_referral"),
                ))

    # Phase 7: Consent (skip if already given on cover page)
    turns.append(Turn(
        id="consent",
        avery_messages=["Almost done — just need your okay on a few things."],
        input_type="inline_card",
        card_type="consent",
        required=True,
        condition=lambda data, modules: not data.get("_consent_given"),
    ))

    # Filter out turns that don't apply based on conditions
    return [t for t in turns if t.condition is None or t.condition(data, modules)]


def find_current_turn(turns: list[Turn], completed_ids: set) -> Turn | None:
    """Find the first unanswered turn."""
    for turn in turns:
        if turn.id not in completed_ids:
            return turn
    return None


def _is_valid_date(raw: str) -> bool:
    """Check if a string can be parsed as a date."""
    try:
        parse_date(raw.strip(), dayfirst=False)
        return True
    except (ParserError, ValueError):
        return False


def _upsert_household_member(data, role, first_name, last_name, dob):
    """Create or update a household member."""
    members = data.setdefault("household_members", [])
    existing = next((m for m in members if m.get("role") == role), None)

    if existing:
        existing["first_name"] = first_name.strip()
        if last_name:
            existing["last_name"] = last_name.strip()
        if dob:
            existing["date_of_birth"] = dob
    else:
        temp_id = role if role in ("primary", "spouse") else f"member-{secrets.token_hex(4)}"
        members.append({
            "temp_id": temp_id,
            "role": role,
            "first_name": first_name.strip(),
            "last_name": last_name or "",
            "date_of_birth": dob or "",
            "needs_coverage": True,
            "other_coverage_access": False,
            "tobacco_user": False,
            "takes_prescriptions": False,
        })
    return None


def _update_household_member_field(data, temp_id, field, value):
    """Update a field on a household member."""
    members = data.get("household_members", [])
    member = next((m for m in members if m.get("temp_id") == temp_id), None)
    if member:
        member[field] = value
    return None


def _create_new_dependent(data, index, first_name, last_name, dob):
    """Create a new dependent household member."""
    temp_id = f"member-{secrets.token_hex(4)}"
    data.setdefault("household_members", []).append({
        "temp_id": temp_id,
        "role": "dependent",
        "first_name": first_name.strip(),
        "last_name": last_name or "",
        "date_of_birth": dob or "",
        "needs_coverage": True,
        "other_coverage_access": False,
        "tobacco_user": False,
        "takes_prescriptions": False,
    })
    return None


def _handle_add_dependent(data, answer):
    """Handle the 'add another dependent' choice."""
    if answer == "add":
        # Signal to insert new dependent turns (handled by build_turns)
        pass
    return None


def _dependent_turns(index: int, temp_id: str) -> list[Turn]:
    """Generate the three turns for a specific dependent."""
    return [
        Turn(
            id=f"dep_{index}_first_name",
            avery_messages=[f"First name for dependent {index + 1}?"],
            input_type="text",
            placeholder="First name",
            required=True,
        ),
        Turn(
            id=f"dep_{index}_last_name",
            avery_messages=["Last name?"],
            input_type="text",
            placeholder="Last name",
        ),
        Turn(
            id=f"dep_{index}_dob",
            avery_messages=["Their date of birth?"],
            input_type="date",
            placeholder="MM/DD/YYYY",
            required=True,
        ),
    ]


def _all_members_for_prescriptions(data: dict) -> list[dict]:
    """Return primary + household_members list for prescription turns."""
    primary = {
        "temp_id": "primary",
        "role": "primary",
        "first_name": data.get("basic_info", {}).get("first_name", "You"),
    }
    others = data.get("household_members", [])
    return [primary] + list(others)
