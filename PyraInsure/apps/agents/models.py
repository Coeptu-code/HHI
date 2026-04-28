from django.conf import settings
from django.db import models


class AgentProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="agent_profile")
    agency_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        label = self.user.get_full_name() or self.user.get_username()
        return f"{label}"

