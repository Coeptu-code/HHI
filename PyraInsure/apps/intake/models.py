from django.conf import settings
from django.db import models

from apps.agents.models import AgentProfile
from apps.customers.models import CustomerRecord
from apps.questionnaires.models import QuestionnaireLink


class IntakeSubmission(models.Model):
    STATUS_CHOICES = [
        ("started", "Started"),
        ("in_progress", "In Progress"),
        ("submitted", "Submitted"),
        ("reviewed", "Reviewed"),
        ("archived", "Archived"),
    ]

    questionnaire_link = models.ForeignKey(QuestionnaireLink, on_delete=models.PROTECT, related_name="submissions")
    agent = models.ForeignKey(AgentProfile, on_delete=models.PROTECT, related_name="submissions")
    customer = models.ForeignKey(CustomerRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="submissions")

    consent_terms = models.BooleanField(default=False)
    consent_privacy = models.BooleanField(default=False)
    consent_contact = models.BooleanField(default=False)
    consent_referral_sharing = models.BooleanField(default=False)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="in_progress")
    public_token = models.CharField(max_length=128, unique=True, null=True, blank=True)
    source = models.CharField(max_length=80, null=True, blank=True)
    score_access_token = models.CharField(max_length=128, unique=True, null=True, blank=True)
    score_viewed_at = models.DateTimeField(null=True, blank=True)
    review_status = models.CharField(
        max_length=20,
        choices=[("unreviewed", "Unreviewed"), ("reviewed", "Reviewed"), ("needs_follow_up", "Needs Follow Up")],
        default="unreviewed",
        db_index=True,
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_intake_submissions",
    )
    review_notes = models.TextField(blank=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["agent", "created_at"]),
            models.Index(fields=["submitted_at"]),
        ]

    def __str__(self) -> str:
        return f"Submission {self.id}"


class IntakeAnswer(models.Model):
    submission = models.ForeignKey(IntakeSubmission, on_delete=models.CASCADE, related_name="answers")
    customer = models.ForeignKey(
        CustomerRecord,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="intake_answers",
    )
    module = models.CharField(max_length=32, blank=True)
    supports = models.CharField(max_length=255, blank=True)
    question_key = models.CharField(max_length=128)
    question_text = models.CharField(max_length=512, null=True, blank=True)
    answer_value = models.TextField(blank=True)
    normalized_value = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["submission", "question_key"]),
            models.Index(fields=["customer"]),
        ]

    def __str__(self) -> str:
        return f"{self.question_key}"


class HouseholdMember(models.Model):
    ROLE_CHOICES = [
        ("primary", "Primary"),
        ("spouse", "Spouse"),
        ("dependent", "Dependent"),
        ("other", "Other"),
    ]

    submission = models.ForeignKey(
        IntakeSubmission,
        on_delete=models.CASCADE,
        related_name="household_members",
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(
        CustomerRecord,
        on_delete=models.SET_NULL,
        related_name="household_members",
        null=True,
        blank=True,
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    name = models.CharField(max_length=255, blank=True)
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120, blank=True)
    date_of_birth = models.DateField()
    dob = models.DateField(null=True, blank=True)
    age = models.PositiveSmallIntegerField(null=True, blank=True)
    needs_health_coverage = models.BooleanField(null=True, blank=True)
    has_prescriptions = models.BooleanField(null=True, blank=True)
    notes = models.TextField(blank=True)
    needs_coverage = models.BooleanField(default=True)
    other_coverage_access = models.BooleanField(default=False)
    legal_parent_guardian_under_19 = models.BooleanField(default=False)
    claimed_tax_dependent = models.BooleanField(default=False)
    pregnant = models.BooleanField(default=False)
    tobacco_user = models.BooleanField(default=False)
    takes_prescriptions = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name or f"{self.first_name} {self.last_name}".strip()


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
