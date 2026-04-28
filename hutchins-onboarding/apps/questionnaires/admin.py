from django.contrib import admin

from .models import QuestionnaireLink


@admin.register(QuestionnaireLink)
class QuestionnaireLinkAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "token", "is_active", "expires_at", "completed_at", "created_at")
    list_filter = ("is_active", "include_health", "include_life", "include_auto", "include_home", "include_umbrella")
    search_fields = ("token", "agent__user__username", "agent__user__email")

# Register your models here.
