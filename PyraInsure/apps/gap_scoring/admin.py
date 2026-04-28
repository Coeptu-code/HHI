from django.contrib import admin

from .models import GapFinding


@admin.register(GapFinding)
class GapFindingAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "customer", "category", "severity", "points", "assigned_to", "created_at")
    list_filter = ("category", "severity", "assigned_to")
    search_fields = ("title", "description")

# Register your models here.
