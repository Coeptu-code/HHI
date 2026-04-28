from django.contrib import admin

from .models import AgentProfile


@admin.register(AgentProfile)
class AgentProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "agency_name", "phone", "created_at")
    search_fields = ("user__username", "user__email", "agency_name", "phone")

# Register your models here.
