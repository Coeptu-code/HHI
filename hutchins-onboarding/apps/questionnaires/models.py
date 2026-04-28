import secrets

from django.db import models
from django.utils import timezone

from apps.agents.models import AgentProfile


def _default_token() -> str:
    return secrets.token_urlsafe(24)


class QuestionnaireLink(models.Model):
    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="questionnaire_links")
    token = models.CharField(max_length=64, unique=True, default=_default_token)

    include_health = models.BooleanField(default=True)
    include_life = models.BooleanField(default=True)
    include_auto = models.BooleanField(default=True)
    include_home = models.BooleanField(default=True)
    include_umbrella = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at <= timezone.now())

    def can_use(self) -> bool:
        return self.is_active and (not self.is_expired()) and (self.completed_at is None)

    def selected_modules(self) -> list[str]:
        modules: list[str] = []
        if self.include_health:
            modules.append("health")
        if self.include_life:
            modules.append("life")
        if self.include_auto:
            modules.append("auto")
        if self.include_home:
            modules.append("home")
        if self.include_umbrella:
            modules.append("umbrella")
        return modules

    def __str__(self) -> str:
        return f"Link {self.token}"
