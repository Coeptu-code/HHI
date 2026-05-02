from django.contrib import admin

from .models import GapFinding, ProductAvailability, RuleConfig, ScoringWeight, TalkingPoint, TalkingPointTemplate


@admin.register(GapFinding)
class GapFindingAdmin(admin.ModelAdmin):
    list_display = ("id", "submission", "customer", "finding_type", "category", "severity", "status", "is_generated", "assigned_to", "created_at")
    list_filter = ("category", "severity", "status", "is_generated", "assigned_to")
    search_fields = ("title", "description", "explanation")


@admin.register(TalkingPoint)
class TalkingPointAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "intake_session", "title", "priority", "category", "status", "created_at")
    list_filter = ("status", "category")
    search_fields = ("title", "hook", "suggested_script")


@admin.register(RuleConfig)
class RuleConfigAdmin(admin.ModelAdmin):
    list_display = ("rule_key", "title", "category", "enabled", "severity", "points", "updated_at")
    list_filter = ("enabled", "category", "severity")
    search_fields = ("rule_key", "title", "description")


@admin.register(ScoringWeight)
class ScoringWeightAdmin(admin.ModelAdmin):
    list_display = ("weight_key", "label", "value", "enabled", "updated_at")
    list_filter = ("enabled",)
    search_fields = ("weight_key", "label")


@admin.register(TalkingPointTemplate)
class TalkingPointTemplateAdmin(admin.ModelAdmin):
    list_display = ("template_key", "finding_type", "title", "category", "enabled", "updated_at")
    list_filter = ("enabled", "category")
    search_fields = ("template_key", "finding_type", "title")


@admin.register(ProductAvailability)
class ProductAvailabilityAdmin(admin.ModelAdmin):
    list_display = ("state", "coverage_type", "carrier", "product_name", "status", "updated_at")
    list_filter = ("state", "coverage_type", "status")
    search_fields = ("carrier", "product_name")
