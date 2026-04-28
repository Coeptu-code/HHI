from django.contrib import admin

from .models import ReferralOpportunity


@admin.register(ReferralOpportunity)
class ReferralOpportunityAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "customer", "category", "severity", "status", "created_at", "updated_at")
    list_filter = ("category", "severity", "status")
    search_fields = ("notes",)

# Register your models here.
