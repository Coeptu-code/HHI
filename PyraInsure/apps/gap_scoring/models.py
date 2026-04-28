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

    submission = models.ForeignKey(IntakeSubmission, on_delete=models.CASCADE, related_name="gap_findings")
    customer = models.ForeignKey(CustomerRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="gap_findings")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    points = models.IntegerField(default=0)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    assigned_to = models.CharField(max_length=20, choices=ASSIGNED_TO_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.category}:{self.severity}:{self.title}"

