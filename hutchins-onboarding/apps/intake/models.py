from django.db import models

from apps.agents.models import AgentProfile
from apps.customers.models import CustomerRecord
from apps.questionnaires.models import QuestionnaireLink


class IntakeSubmission(models.Model):
    STATUS_CHOICES = [
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
    ]

    questionnaire_link = models.ForeignKey(QuestionnaireLink, on_delete=models.PROTECT, related_name="submissions")
    agent = models.ForeignKey(AgentProfile, on_delete=models.PROTECT, related_name="submissions")
    customer = models.ForeignKey(CustomerRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions")

    consent_terms = models.BooleanField(default=False)
    consent_privacy = models.BooleanField(default=False)
    consent_contact = models.BooleanField(default=False)
    consent_referral_sharing = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_progress")
    score_access_token = models.CharField(max_length=128, unique=True, null=True, blank=True)
    score_viewed_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Submission {self.id}"


class IntakeAnswer(models.Model):
    submission = models.ForeignKey(IntakeSubmission, on_delete=models.CASCADE, related_name="answers")
    module = models.CharField(max_length=32, blank=True)
    supports = models.CharField(max_length=255, blank=True)
    question_key = models.CharField(max_length=128)
    question_text = models.CharField(max_length=512)
    answer_value = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.question_key}"


class HouseholdMember(models.Model):
    ROLE_CHOICES = [
        ("primary", "Primary"),
        ("spouse", "Spouse"),
        ("dependent", "Dependent"),
    ]

    submission = models.ForeignKey(
        IntakeSubmission,
        on_delete=models.CASCADE,
        related_name="household_members",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True)
    date_of_birth = models.DateField()
    needs_coverage = models.BooleanField(default=True)
    other_coverage_access = models.BooleanField(default=False)
    legal_parent_guardian_under_19 = models.BooleanField(default=False)
    claimed_tax_dependent = models.BooleanField(default=False)
    pregnant = models.BooleanField(default=False)
    tobacco_user = models.BooleanField(default=False)
    takes_prescriptions = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()


class PrescriptionMedication(models.Model):
    submission = models.ForeignKey(
        IntakeSubmission,
        on_delete=models.CASCADE,
        related_name="prescription_medications",
    )
    household_member = models.ForeignKey(
        HouseholdMember,
        on_delete=models.CASCADE,
        related_name="prescription_medications",
    )
    drug_id = models.CharField(max_length=100, blank=True)
    drug_name = models.CharField(max_length=255)
    normalized_drug_name = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=50, default="rxterms")
    dosage_strength = models.CharField(max_length=100, blank=True)
    frequency = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.drug_name
