from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any

import requests


_SPACE_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[^\w\s#\-]")
_ABBREVIATIONS = {
    "ln": "lane",
    "ave": "avenue",
    "av": "avenue",
    "rd": "road",
    "st": "street",
    "dr": "drive",
    "ctr": "center",
    "blvd": "boulevard",
    "hwy": "highway",
    "pkwy": "parkway",
    "cir": "circle",
    "ct": "court",
    "pl": "place",
}


@dataclass(frozen=True)
class AddressSuggestion:
    street: str
    city: str
    state: str
    zip_code: str
    formatted: str
    confidence: float
    source: str = "census"

    def as_dict(self) -> dict[str, Any]:
        return {
            "street": self.street,
            "city": self.city,
            "state": self.state,
            "zip_code": self.zip_code,
            "formatted": self.formatted,
            "confidence": self.confidence,
            "source": self.source,
        }


def normalize_address_input(raw: str) -> str:
    cleaned = _SPACE_RE.sub(" ", (raw or "").strip())
    cleaned = _PUNCT_RE.sub("", cleaned)
    tokens = cleaned.lower().split(" ")
    expanded_tokens = [_ABBREVIATIONS.get(token, token) for token in tokens if token]

    title_tokens: list[str] = []
    for token in expanded_tokens:
        if token.isdigit():
            title_tokens.append(token)
            continue
        pieces = token.split("-")
        titled_pieces = []
        for piece in pieces:
            subpieces = piece.split("'")
            titled_pieces.append("'".join(part[:1].upper() + part[1:] for part in subpieces))
        title_tokens.append("-".join(titled_pieces))
    return " ".join(title_tokens)


class AddressLookupProvider:
    def lookup_address(self, query: str, zip_code: str | None = None, state: str | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def normalize_address(self, raw_address: str, zip_code: str | None = None, state: str | None = None) -> dict[str, Any]:
        cleaned = normalize_address_input(raw_address)
        return self.lookup_address(cleaned, zip_code=zip_code, state=state)


class StubAddressProvider(AddressLookupProvider):
    def lookup_address(self, query: str, zip_code: str | None = None, state: str | None = None) -> dict[str, Any]:
        normalized = normalize_address_input(query)
        if not normalized:
            return {"status": "no_match", "suggestions": []}

        if "Dalton Lane" in normalized:
            suggestion = AddressSuggestion(
                street="34 Dalton Ave",
                city="Worcester",
                state=(state or "MA").upper(),
                zip_code=(zip_code or "01604")[:5],
                formatted=f"34 Dalton Ave, Worcester, {(state or 'MA').upper()} {(zip_code or '01604')[:5]}",
                confidence=0.92,
                source="stub",
            )
            return {"status": "confirmed", "suggestions": [suggestion.as_dict()]}

        suggestion = AddressSuggestion(
            street=normalized,
            city="",
            state=(state or "").upper(),
            zip_code=(zip_code or "")[:5],
            formatted=", ".join([part for part in [normalized, (state or "").upper(), (zip_code or "")[:5]] if part]),
            confidence=0.5,
            source="stub",
        )
        return {"status": "needs_confirmation", "suggestions": [suggestion.as_dict()]}


class CensusAddressProvider(AddressLookupProvider):
    URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"

    def lookup_address(self, query: str, zip_code: str | None = None, state: str | None = None) -> dict[str, Any]:
        if not query.strip():
            return {"status": "no_match", "suggestions": []}

        location = query.strip()
        locality_parts = [part for part in [state, zip_code] if part]
        if locality_parts:
            location = f"{location}, {' '.join(locality_parts)}"

        try:
            response = requests.get(
                self.URL,
                params={
                    "address": location,
                    "benchmark": "Public_AR_Current",
                    "format": "json",
                },
                timeout=6,
            )
            response.raise_for_status()
            payload = response.json()
        except Exception:
            return {"status": "no_match", "suggestions": []}

        matches = payload.get("result", {}).get("addressMatches", []) or []
        suggestions: list[AddressSuggestion] = []
        for index, match in enumerate(matches[:3]):
            components = match.get("addressComponents", {}) or {}
            matched_address = str(match.get("matchedAddress") or "").strip()
            street = str(components.get("streetName") or "").strip()
            if components.get("fromAddress"):
                street = f"{components.get('fromAddress')} {street}".strip()
            city = str(components.get("city") or "").strip()
            matched_state = str(components.get("state") or state or "").strip().upper()
            matched_zip = str(components.get("zip") or zip_code or "").strip()[:5]
            confidence = max(0.0, 1.0 - (index * 0.1))
            formatted = matched_address or ", ".join([part for part in [street, city, matched_state, matched_zip] if part])
            suggestions.append(
                AddressSuggestion(
                    street=street or formatted,
                    city=city,
                    state=matched_state,
                    zip_code=matched_zip,
                    formatted=formatted,
                    confidence=confidence,
                    source="census",
                )
            )

        if not suggestions:
            return {"status": "no_match", "suggestions": []}
        if len(suggestions) > 1:
            return {"status": "multiple_matches", "suggestions": [item.as_dict() for item in suggestions]}
        if suggestions[0].confidence >= 0.85:
            return {"status": "confirmed", "suggestions": [suggestions[0].as_dict()]}
        return {"status": "needs_confirmation", "suggestions": [suggestions[0].as_dict()]}


def get_address_provider() -> AddressLookupProvider:
    provider_name = os.getenv("ADDRESS_LOOKUP_PROVIDER", "census").strip().lower()
    if provider_name == "stub":
        return StubAddressProvider()
    return CensusAddressProvider()

