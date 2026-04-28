from django.db import models

from apps.agents.models import AgentProfile


class CustomerRecord(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.first_name} {self.last_name}".strip()

