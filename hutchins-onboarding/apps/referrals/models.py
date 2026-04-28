from django.db import models

from apps.customers.models import CustomerRecord
from apps.intake.models import IntakeSubmission


class ReferralOpportunity(models.Model):
    CATEGORY_CHOICES = [
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

    STATUS_CHOICES = [
        ("possible_opportunity", "Possible Opportunity"),
        ("ready_to_refer", "Ready To Refer"),
        ("referred", "Referred"),
        ("closed", "Closed"),
    ]

    submission = models.ForeignKey(IntakeSubmission, on_delete=models.CASCADE, related_name="referral_opportunities")
    customer = models.ForeignKey(CustomerRecord, on_delete=models.SET_NULL, null=True, blank=True, related_name="referral_opportunities")
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default="possible_opportunity")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.category}:{self.status}"

