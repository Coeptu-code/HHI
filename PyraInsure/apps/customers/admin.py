from django.contrib import admin

from .models import AgentNote, CoverageItem, CustomerActivity, CustomerRecord, PreCallSummary


@admin.register(CustomerRecord)
class CustomerRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "first_name", "last_name", "email", "phone", "state", "status", "created_at")
    list_filter = ("status", "state")
    search_fields = ("first_name", "last_name", "email", "phone")


@admin.register(CoverageItem)
class CoverageItemAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "coverage_type", "status", "carrier", "plan_name", "created_at")
    list_filter = ("coverage_type", "status")
    search_fields = ("customer__first_name", "customer__last_name", "carrier", "plan_name", "gap_label")


@admin.register(CustomerActivity)
class CustomerActivityAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "activity_type", "title", "actor_type", "actor_name", "created_at")
    list_filter = ("activity_type", "actor_type")
    search_fields = ("customer__first_name", "customer__last_name", "title", "description", "actor_name")


@admin.register(AgentNote)
class AgentNoteAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "note_type", "created_by", "created_at")
    list_filter = ("note_type",)
    search_fields = ("customer__first_name", "customer__last_name", "note")


@admin.register(PreCallSummary)
class PreCallSummaryAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "generated_at", "avery_read", "created_at")
    search_fields = ("customer__first_name", "customer__last_name", "summary_text")
