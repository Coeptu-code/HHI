from __future__ import annotations

import re
from datetime import date

from django import forms

from .models import Client


DOCUMENT_TYPE_CHOICES = [
    ("handwritten_note", "Handwritten Note"),
    ("policy", "Policy"),
]


class MultipleFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True

    def __init__(self, *args, **kwargs):
        attrs = kwargs.setdefault("attrs", {})
        attrs.setdefault("class", "form-control")
        super().__init__(*args, **kwargs)


class MultipleFileField(forms.FileField):
    widget = MultipleFileInput

    def clean(self, data, initial=None):
        single_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_clean(item, initial) for item in data]
        return [single_clean(data, initial)]


class DocumentUploadForm(forms.Form):
    client = forms.ModelChoiceField(
        queryset=Client.objects.all(),
        required=False,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    document_type = forms.ChoiceField(
        choices=DOCUMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".pdf,image/*,.heic,.heif",
                "aria-label": "Single file",
            }
        ),
    )
    files = MultipleFileField(
        required=False,
        widget=MultipleFileInput(
            attrs={
                "class": "form-control",
                "accept": "image/*,.heic,.heif",
                "aria-label": "Multiple images",
            }
        ),
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
    )

    def clean(self):
        cleaned = super().clean()
        document_type = cleaned.get("document_type")
        file = cleaned.get("file")
        files = cleaned.get("files") or []

        if document_type == "handwritten_note":
            if not file:
                raise forms.ValidationError("Handwritten Note requires a single file upload.")
            if files:
                raise forms.ValidationError("Handwritten Note only accepts one file.")

        if document_type == "policy":
            if file and files:
                raise forms.ValidationError("Policy accepts either one PDF or multiple images, not both.")
            if not file and not files:
                raise forms.ValidationError("Policy requires either one PDF or one or more images.")

        return cleaned


class ClientIntakeForm(forms.ModelForm):
    class MMDDYYYYDateField(forms.DateField):
        default_error_messages = {
            "invalid": "Enter a valid date in MM/DD/YYYY format.",
        }

        def to_python(self, value):
            if isinstance(value, date) or value is None:
                return value

            raw = (value or "").strip()
            if not raw:
                return None

            if re.fullmatch(r"\d{8}", raw):
                raw = f"{raw[0:2]}/{raw[2:4]}/{raw[4:8]}"

            return super().to_python(raw.replace("-", "/"))

    dob = MMDDYYYYDateField(
        required=False,
        input_formats=["%m/%d/%Y", "%m-%d-%Y", "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%y", "%m-%d-%y"],
        widget=forms.DateInput(
            format="%m/%d/%Y",
            attrs={
                "class": "form-control",
                "placeholder": "MM/DD/YYYY",
                "maxlength": "10",
                "inputmode": "numeric",
                "autocomplete": "bday",
            },
        ),
    )

    policy_pdf = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".pdf,application/pdf",
                "aria-label": "Policy PDF",
            }
        ),
    )
    policy_images = MultipleFileField(
        required=False,
        widget=MultipleFileInput(
            attrs={
                "class": "form-control",
                "accept": "image/*,.heic,.heif",
                "aria-label": "Policy images",
            }
        ),
    )
    policy_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    handwritten_note_file = forms.FileField(
        required=False,
        widget=forms.ClearableFileInput(
            attrs={
                "class": "form-control",
                "accept": ".pdf,image/*,.heic,.heif",
                "aria-label": "Handwritten note",
            }
        ),
    )
    handwritten_note_notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 2}),
    )

    class Meta:
        model = Client
        fields = [
            "full_name",
            "dob",
            "phone_number",
            "email",
            "income",
            "address",
            "city",
            "state",
            "zip_code",
            "notes",
        ]
        widgets = {
            "full_name": forms.TextInput(attrs={"class": "form-control"}),
            "phone_number": forms.TextInput(attrs={"class": "form-control"}),
            "email": forms.EmailInput(attrs={"class": "form-control"}),
            "income": forms.TextInput(attrs={"class": "form-control"}),
            "address": forms.TextInput(attrs={"class": "form-control"}),
            "city": forms.TextInput(attrs={"class": "form-control"}),
            "state": forms.TextInput(attrs={"class": "form-control"}),
            "zip_code": forms.TextInput(attrs={"class": "form-control", "maxlength": "10"}),
            "notes": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
        }

    def clean(self):
        cleaned = super().clean()
        policy_pdf = cleaned.get("policy_pdf")
        policy_images = cleaned.get("policy_images") or []

        if policy_pdf and policy_images:
            raise forms.ValidationError("Upload either one policy PDF or policy images, not both.")

        return cleaned

    def clean_full_name(self):
        full_name = (self.cleaned_data.get("full_name") or "").strip()
        if not full_name:
            raise forms.ValidationError("Full name is required.")
        return full_name


ATTACHMENT_DOCUMENT_TYPE_CHOICES = [
    ("policy", "Policy"),
    ("handwritten_note", "Handwritten Note"),
    ("other", "Other"),
]


class ClientAttachmentUploadForm(forms.Form):
    document_type = forms.ChoiceField(
        choices=ATTACHMENT_DOCUMENT_TYPE_CHOICES,
        widget=forms.Select(attrs={"class": "form-control"}),
    )
    display_name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )
