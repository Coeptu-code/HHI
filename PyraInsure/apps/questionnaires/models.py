import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.agents.models import AgentProfile


def _default_token() -> str:
    return secrets.token_urlsafe(24)


class QuestionnaireLink(models.Model):
    MODULE_KEYS = ("health", "life", "auto", "home", "umbrella")
    STATUS_CHOICES = [
        ("created", "Created"),
        ("sent", "Sent"),
        ("started", "Started"),
        ("submitted", "Submitted"),
        ("archived", "Archived"),
    ]

    agent = models.ForeignKey(AgentProfile, on_delete=models.CASCADE, related_name="questionnaire_links")
    customer = models.ForeignKey(
        "customers.CustomerRecord",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="questionnaire_links",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_questionnaire_links",
    )
    token = models.CharField(max_length=64, unique=True, default=_default_token)

    include_health = models.BooleanField(default=True)
    include_life = models.BooleanField(default=True)
    include_auto = models.BooleanField(default=True)
    include_home = models.BooleanField(default=True)
    include_umbrella = models.BooleanField(default=True)

    is_active = models.BooleanField(default=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="created", db_index=True)
    delivery_method = models.CharField(max_length=20, null=True, blank=True)
    module_order = models.JSONField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    last_opened_at = models.DateTimeField(null=True, blank=True)
    open_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self) -> bool:
        return bool(self.expires_at and self.expires_at <= timezone.now())

    def can_use(self) -> bool:
        return self.is_active and self.status != "archived" and (not self.is_expired()) and (self.completed_at is None)

    def selected_modules(self) -> list[str]:
        enabled_modules: list[str] = []
        if self.include_health:
            enabled_modules.append("health")
        if self.include_life:
            enabled_modules.append("life")
        if self.include_auto:
            enabled_modules.append("auto")
        if self.include_home:
            enabled_modules.append("home")
        if self.include_umbrella:
            enabled_modules.append("umbrella")

        raw_order = self.module_order or []
        normalized_order: list[str] = []
        for item in raw_order:
            module = str(item or "").strip().lower()
            if module not in self.MODULE_KEYS:
                continue
            if module in normalized_order:
                continue
            normalized_order.append(module)

        ordered_enabled = [module for module in normalized_order if module in enabled_modules]
        for module in enabled_modules:
            if module not in ordered_enabled:
                ordered_enabled.append(module)
        return ordered_enabled

    def __str__(self) -> str:
        return f"Link {self.token}"
