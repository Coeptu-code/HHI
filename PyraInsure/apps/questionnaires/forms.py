from __future__ import annotations

import json
from typing import Any

from django import forms

from apps.questionnaires.models import QuestionnaireLink


class QuestionnaireLinkCreateForm(forms.ModelForm):
    client_name = forms.CharField(max_length=255, required=False)
    phone = forms.CharField(max_length=50, required=False)
    module_order = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = QuestionnaireLink
        fields = [
            "client_name",
            "phone",
            "include_health",
            "include_life",
            "include_auto",
            "include_home",
            "include_umbrella",
            "module_order",
        ]
        labels = {
            "include_health": "Health Intake",
            "include_life": "Life Gap Check",
            "include_auto": "Auto Gap Check",
            "include_home": "Home Gap Check",
            "include_umbrella": "Umbrella Gap Check",
        }

    def clean_client_name(self) -> str:
        return str(self.cleaned_data.get("client_name") or "").strip()

    def clean_phone(self) -> str:
        return str(self.cleaned_data.get("phone") or "").strip()

    def clean_module_order(self) -> list[str]:
        raw_value = self.cleaned_data.get("module_order")
        if raw_value in (None, ""):
            return []

        parsed: Any = raw_value
        if isinstance(raw_value, str):
            try:
                parsed = json.loads(raw_value)
            except json.JSONDecodeError:
                parsed = [item.strip() for item in raw_value.split(",") if item.strip()]

        if not isinstance(parsed, list):
            raise forms.ValidationError("Module order must be a list.")

        normalized: list[str] = []
        for item in parsed:
            module = str(item or "").strip().lower()
            if module not in QuestionnaireLink.MODULE_KEYS:
                continue
            if module in normalized:
                continue
            normalized.append(module)
        return normalized

    def clean(self) -> dict[str, Any]:
        cleaned = super().clean()
        enabled_modules = {
            "health": bool(cleaned.get("include_health")),
            "life": bool(cleaned.get("include_life")),
            "auto": bool(cleaned.get("include_auto")),
            "home": bool(cleaned.get("include_home")),
            "umbrella": bool(cleaned.get("include_umbrella")),
        }
        if not any(enabled_modules.values()):
            raise forms.ValidationError("Select at least one module.")

        module_order = cleaned.get("module_order") or []
        cleaned["module_order"] = [
            module
            for module in module_order
            if enabled_modules.get(module, False)
        ]
        return cleaned
