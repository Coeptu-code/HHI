from django import forms

from apps.questionnaires.models import QuestionnaireLink


class QuestionnaireLinkCreateForm(forms.ModelForm):
    class Meta:
        model = QuestionnaireLink
        fields = [
            "include_health",
            "include_life",
            "include_auto",
            "include_home",
            "include_umbrella",
        ]
        labels = {
            "include_health": "Health Intake",
            "include_life": "Life Gap Check",
            "include_auto": "Auto Gap Check",
            "include_home": "Home Gap Check",
            "include_umbrella": "Umbrella Gap Check",
        }

    def clean(self):
        cleaned = super().clean()
        flags = [
            cleaned.get("include_health"),
            cleaned.get("include_life"),
            cleaned.get("include_auto"),
            cleaned.get("include_home"),
            cleaned.get("include_umbrella"),
        ]
        if not any(flags):
            raise forms.ValidationError("Select at least one module.")
        return cleaned
