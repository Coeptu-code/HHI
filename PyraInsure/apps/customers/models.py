from django.conf import settings
from django.db import models

from apps.agents.models import AgentProfile


class CustomerRecord(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("prospect", "Prospect"),
        ("inactive", "Inactive"),
        ("archived", "Archived"),
    ]

    CONTACT_METHOD_CHOICES = [
        ("phone", "Phone"),
        ("email", "Email"),
        ("text", "Text"),
    ]

    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="customers")
    first_name = models.CharField(max_length=120)
    last_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    state = models.CharField(max_length=2, blank=True)
    preferred_contact_method = models.CharField(max_length=20, choices=CONTACT_METHOD_CHOICES, blank=True)
    client_since = models.DateField(null=True, blank=True)
    last_submission_at = models.DateTimeField(null=True, blank=True)
    avg_gap_score = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["agent", "status"]),
            models.Index(fields=["last_submission_at"]),
        ]

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def assigned_agent_name(self) -> str:
        return str(self.agent)

    def __str__(self) -> str:
        return self.full_name


class CoverageItem(models.Model):
    COVERAGE_TYPE_CHOICES = [
        ("medical", "Medical"),
        ("dental", "Dental"),
        ("vision", "Vision"),
        ("life", "Life"),
        ("auto_home", "Auto + Home"),
        ("homeowners", "Homeowners"),
        ("umbrella", "Umbrella"),
        ("other", "Other"),
    ]

    STATUS_CHOICES = [
        ("active", "Active"),
        ("gap", "Gap"),
        ("unknown", "Unknown"),
        ("referral_opportunity", "Referral Opportunity"),
        ("inactive", "Inactive"),
    ]

    customer = models.ForeignKey(CustomerRecord, on_delete=models.CASCADE, related_name="coverage_items")
    household_member = models.ForeignKey(
        "intake.HouseholdMember",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="coverage_items",
    )
    coverage_type = models.CharField(max_length=30, choices=COVERAGE_TYPE_CHOICES)
    carrier = models.CharField(max_length=255, blank=True)
    plan_name = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="unknown", db_index=True)
    gap_label = models.CharField(max_length=255, blank=True)
    deductible = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    premium = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["household_member"]),
        ]

    def __str__(self) -> str:
        return f"{self.customer.full_name}: {self.coverage_type}"


class CustomerActivity(models.Model):
    customer = models.ForeignKey(CustomerRecord, on_delete=models.CASCADE, related_name="activities")
    intake_session = models.ForeignKey(
        "intake.IntakeSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="customer_activities",
    )
    activity_type = models.CharField(max_length=80)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    actor_type = models.CharField(max_length=50, blank=True)
    actor_name = models.CharField(max_length=255, blank=True)
    metadata = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "created_at"]),
            models.Index(fields=["intake_session"]),
        ]

    def __str__(self) -> str:
        return f"{self.customer.full_name}: {self.title}"


class AgentNote(models.Model):
    NOTE_TYPE_CHOICES = [
        ("general", "General"),
        ("do_not_bring_up", "Do Not Bring Up"),
        ("call_prep", "Call Prep"),
        ("follow_up", "Follow Up"),
    ]

    customer = models.ForeignKey(CustomerRecord, on_delete=models.CASCADE, related_name="agent_notes")
    intake_session = models.ForeignKey(
        "intake.IntakeSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="agent_notes",
    )
    note = models.TextField()
    note_type = models.CharField(max_length=20, choices=NOTE_TYPE_CHOICES, default="general", db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_agent_notes",
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "note_type"]),
            models.Index(fields=["intake_session"]),
        ]

    def __str__(self) -> str:
        return f"{self.customer.full_name}: {self.note_type}"


class PreCallSummary(models.Model):
    customer = models.ForeignKey(CustomerRecord, on_delete=models.CASCADE, related_name="pre_call_summaries")
    intake_session = models.ForeignKey(
        "intake.IntakeSubmission",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pre_call_summaries",
    )
    summary_text = models.TextField(blank=True)
    avery_read = models.TextField(null=True, blank=True)
    talking_point_order = models.JSONField(null=True, blank=True)
    do_not_bring_up = models.JSONField(null=True, blank=True)
    generated_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "generated_at"]),
            models.Index(fields=["intake_session"]),
        ]

    def __str__(self) -> str:
        return f"Pre-call summary for {self.customer.full_name}"
