from django.db import models

from apps.customers.models import CustomerRecord
from apps.intake.models import IntakeSubmission


class GapFinding(models.Model):
    CATEGORY_CHOICES = [
        ("health", "Health"),
        ("life", "Life"),
        ("auto", "Auto"),
        ("home", "Home"),
        ("umbrella", "Umbrella"),
    ]

    SEVERITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]

    ASSIGNED_TO_CHOICES = [
        ("hutchins", "Hutchins"),
        ("partner_referral", "Partner Referral"),
    ]

    STATUS_CHOICES = [
        ("open", "Open"),
        ("dismissed", "Dismissed"),
        ("resolved", "Resolved"),
    ]

    submission = models.ForeignKey(
        IntakeSubmission,
        on_delete=models.CASCADE,
        related_name="gap_findings",
        null=True,
        blank=True,
    )
    customer = models.ForeignKey(CustomerRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="gap_findings")
    finding_type = models.CharField(max_length=64, blank=True)
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, db_index=True)
    points = models.IntegerField(default=0)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    explanation = models.TextField(blank=True)
    source_answer_ids = models.JSONField(null=True, blank=True)
    is_generated = models.BooleanField(default=True, db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="open", db_index=True)
    assigned_to = models.CharField(max_length=20, choices=ASSIGNED_TO_CHOICES, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "status"]),
            models.Index(fields=["submission"]),
        ]

    def __str__(self) -> str:
        return f"{self.category}:{self.severity}:{self.title}"


class TalkingPoint(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("dismissed", "Dismissed"),
        ("used", "Used"),
    ]

    customer = models.ForeignKey(CustomerRecord, on_delete=models.CASCADE, related_name="talking_points")
    intake_session = models.ForeignKey(
        IntakeSubmission,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="talking_points",
    )
    title = models.CharField(max_length=255)
    priority = models.IntegerField(default=0)
    category = models.CharField(max_length=80, blank=True)
    hook = models.TextField(blank=True)
    suggested_script = models.TextField(blank=True)
    quick_facts = models.JSONField(null=True, blank=True)
    related_finding_ids = models.JSONField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active", db_index=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["customer", "priority"]),
            models.Index(fields=["intake_session"]),
        ]

    def __str__(self) -> str:
        return f"{self.customer}: {self.title}"


class RuleConfig(models.Model):
    SEVERITY_CHOICES = [
        ("critical", "Critical"),
        ("high", "High"),
        ("medium", "Medium"),
        ("low", "Low"),
    ]

    rule_key = models.CharField(max_length=100, unique=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    enabled = models.BooleanField(default=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    points = models.IntegerField(default=0)
    config = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["rule_key", "enabled"]),
        ]

    def __str__(self) -> str:
        return self.rule_key


class ScoringWeight(models.Model):
    weight_key = models.CharField(max_length=100, unique=True)
    label = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=10, decimal_places=2)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["weight_key", "enabled"]),
        ]

    def __str__(self) -> str:
        return self.weight_key


class TalkingPointTemplate(models.Model):
    template_key = models.CharField(max_length=100, unique=True)
    finding_type = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255)
    category = models.CharField(max_length=80, blank=True)
    hook = models.TextField(blank=True)
    suggested_script = models.TextField(blank=True)
    quick_facts_template = models.JSONField(null=True, blank=True)
    enabled = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["finding_type", "enabled"]),
        ]

    def __str__(self) -> str:
        return self.template_key


class ProductAvailability(models.Model):
    STATUS_CHOICES = [
        ("available", "Available"),
        ("limited", "Limited"),
        ("unavailable", "Unavailable"),
    ]

    state = models.CharField(max_length=2, db_index=True)
    coverage_type = models.CharField(max_length=80, db_index=True)
    carrier = models.CharField(max_length=255, db_index=True)
    product_name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="available", db_index=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=["state", "coverage_type", "carrier"]),
        ]

    def __str__(self) -> str:
        return f"{self.state}:{self.coverage_type}:{self.carrier}"
