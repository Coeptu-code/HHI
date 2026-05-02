from django.contrib import admin

from .models import QuestionnaireLink


@admin.register(QuestionnaireLink)
class QuestionnaireLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "customer", "token", "status", "delivery_method", "open_count", "is_active", "sent_at", "started_at", "completed_at", "created_at")
    list_filter = ("status", "delivery_method", "is_active", "include_health", "include_life", "include_auto", "include_home", "include_umbrella")
    search_fields = ("token", "agent__user__username", "agent__user__email")

# Register your models here.
