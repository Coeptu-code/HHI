from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date

from dateutil.parser import ParserError, parse as parse_date


_SPACE_RE = re.compile(r"\s+")
_NON_DIGIT_RE = re.compile(r"\D+")
_STATE_NAMES = {
    "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR", "CALIFORNIA": "CA",
    "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE", "FLORIDA": "FL", "GEORGIA": "GA",
    "HAWAII": "HI", "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA",
    "KANSAS": "KS", "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
    "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO",
    "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV", "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ",
    "NEW MEXICO": "NM", "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH",
    "OKLAHOMA": "OK", "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
    "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT", "VERMONT": "VT",
    "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV", "WISCONSIN": "WI", "WYOMING": "WY",
    "DISTRICT OF COLUMBIA": "DC",
}


@dataclass(frozen=True)
class NormalizationResult:
    ok: bool
    normalized: str | None = None
    display: str | None = None
    error: str | None = None


def _collapse_spaces(value: str) -> str:
    return _SPACE_RE.sub(" ", value.strip())


def _title_segment(segment: str) -> str:
    if not segment:
        return ""
    return segment[:1].upper() + segment[1:].lower()


def _smart_title_token(token: str) -> str:
    hyphen_parts = token.split("-")
    titled_hyphen_parts: list[str] = []
    for hyphen_part in hyphen_parts:
        apostrophe_parts = hyphen_part.split("'")
        titled_apostrophe_parts = [_title_segment(part) for part in apostrophe_parts]
        titled_hyphen_parts.append("'".join(titled_apostrophe_parts))
    return "-".join(titled_hyphen_parts)


def normalize_name(raw: str) -> str:
    cleaned = _collapse_spaces(raw)
    if not cleaned:
        return ""
    return " ".join(_smart_title_token(token) for token in cleaned.split(" "))


def detect_possible_full_name(raw: str) -> bool:
    normalized = normalize_name(raw)
    return len(normalized.split(" ")) > 1


def split_full_name(raw: str) -> tuple[str, str]:
    normalized = normalize_name(raw)
    if not normalized:
        return "", ""
    tokens = normalized.split(" ")
    return tokens[0], " ".join(tokens[1:])


def normalize_phone(raw: str) -> NormalizationResult:
    digits = _NON_DIGIT_RE.sub("", raw or "")
    if len(digits) == 11 and digits.startswith("1"):
        digits = digits[1:]
    if len(digits) != 10:
        return NormalizationResult(ok=False, error="That phone number looks off — please enter a 10-digit US number.")
    display = f"({digits[0:3]}) {digits[3:6]}-{digits[6:10]}"
    return NormalizationResult(ok=True, normalized=display, display=display)


def normalize_zip(raw: str) -> NormalizationResult:
    digits = _NON_DIGIT_RE.sub("", raw or "")
    if len(digits) < 5:
        return NormalizationResult(ok=False, error="Please enter a valid 5-digit ZIP code.")
    zip_code = digits[:5]
    return NormalizationResult(ok=True, normalized=zip_code, display=zip_code)


def normalize_state(raw: str) -> NormalizationResult:
    value = _collapse_spaces(raw).upper()
    if not value:
        return NormalizationResult(ok=False, error="Please enter a state.")
    if len(value) == 2 and value.isalpha():
        return NormalizationResult(ok=True, normalized=value, display=value)
    mapped = _STATE_NAMES.get(value)
    if mapped:
        return NormalizationResult(ok=True, normalized=mapped, display=mapped)
    return NormalizationResult(ok=False, error="Please enter a valid U.S. state abbreviation.")


def normalize_email(raw: str) -> NormalizationResult:
    value = _collapse_spaces(raw).lower()
    if not value:
        return NormalizationResult(ok=True, normalized="", display="")
    if "@" not in value or "." not in value.split("@")[-1]:
        return NormalizationResult(ok=False, error="That email looks off — can you re-enter it?")
    return NormalizationResult(ok=True, normalized=value, display=value)


def normalize_income(raw: str) -> NormalizationResult:
    value = _collapse_spaces(raw)
    if not value or value == "__skip__":
        return NormalizationResult(ok=True, normalized="", display="")
    digits = _NON_DIGIT_RE.sub("", value)
    if digits:
        numeric = int(digits)
        return NormalizationResult(ok=True, normalized=str(numeric), display=f"${numeric:,}")
    text = value.lower()
    if text in {"unknown", "prefer not to say", "not sure"}:
        return NormalizationResult(ok=True, normalized="unknown", display="Unknown")
    return NormalizationResult(ok=False, error="Please enter income as a number like 65000.")


def normalize_yes_no(raw: str) -> NormalizationResult:
    text = _collapse_spaces(raw).lower()
    if text in {"yes", "y", "true", "1", "on"}:
        return NormalizationResult(ok=True, normalized="yes", display="Yes")
    if text in {"no", "n", "false", "0", "off"}:
        return NormalizationResult(ok=True, normalized="no", display="No")
    return NormalizationResult(ok=False, error="Please answer yes or no.")


def normalize_liability_limit(raw: str) -> NormalizationResult:
    text = _collapse_spaces(raw).lower()
    mapping = {
        "state_minimum": "low",
        "minimum": "low",
        "low": "low",
        "unknown": "unknown",
        "not sure": "unknown",
        "adequate": "standard",
        "standard": "standard",
        "high": "high",
    }
    if text in mapping:
        normalized = mapping[text]
        return NormalizationResult(ok=True, normalized=normalized, display=normalized.title())
    return NormalizationResult(ok=False, error="Please choose low, standard, high, or unknown.")


def _date_from_digits(raw: str, today: date) -> date | None:
    digits = _NON_DIGIT_RE.sub("", raw or "")
    if len(digits) == 8:
        # MMDDYYYY
        month = int(digits[0:2])
        day = int(digits[2:4])
        year = int(digits[4:8])
        try:
            return date(year, month, day)
        except ValueError:
            # YYYYMMDD fallback
            year = int(digits[0:4])
            month = int(digits[4:6])
            day = int(digits[6:8])
            try:
                return date(year, month, day)
            except ValueError:
                return None
    if len(digits) == 6:
        month = int(digits[0:2])
        day = int(digits[2:4])
        yy = int(digits[4:6])
        pivot = today.year % 100
        year = 2000 + yy if yy <= pivot else 1900 + yy
        try:
            return date(year, month, day)
        except ValueError:
            return None
    return None


def normalize_date(raw: str, *, today: date | None = None) -> NormalizationResult:
    cleaned = _collapse_spaces(raw)
    if not cleaned:
        return NormalizationResult(ok=False, error="Please enter a date of birth.")

    reference_date = today or date.today()

    parsed_date = _date_from_digits(cleaned, reference_date)
    if parsed_date is None:
        try:
            parsed_date = parse_date(cleaned, dayfirst=False, yearfirst=False).date()
        except (ParserError, ValueError):
            return NormalizationResult(
                ok=False,
                error="I couldn't read that date — try MM/DD/YYYY, like 01/05/1990.",
            )

    if parsed_date > reference_date:
        return NormalizationResult(ok=False, error="That date is in the future — can you re-enter your birth date?")

    age_years = reference_date.year - parsed_date.year - (
        (reference_date.month, reference_date.day) < (parsed_date.month, parsed_date.day)
    )
    if age_years < 0:
        return NormalizationResult(ok=False, error="That date is in the future — can you re-enter your birth date?")
    if age_years > 120:
        return NormalizationResult(ok=False, error="Please double-check that birth date.")

    display = parsed_date.strftime("%m/%d/%Y")
    normalized = parsed_date.isoformat()
    return NormalizationResult(ok=True, normalized=normalized, display=display)
