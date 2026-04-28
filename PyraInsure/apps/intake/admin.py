from django.contrib import admin

from .models import HouseholdMember, IntakeAnswer, IntakeSubmission, PrescriptionMedication


class IntakeAnswerInline(admin.TabularInline):
    model = IntakeAnswer
    extra = 0


class HouseholdMemberInline(admin.TabularInline):
    model = HouseholdMember
    extra = 0


class PrescriptionMedicationInline(admin.TabularInline):
    model = PrescriptionMedication
    extra = 0


@admin.register(IntakeSubmission)
class IntakeSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "questionnaire_link", "customer", "status", "submitted_at", "created_at")
    list_filter = ("status",)
    search_fields = ("customer__email", "customer__first_name", "customer__last_name", "questionnaire_link__token")
    inlines = [HouseholdMemberInline, PrescriptionMedicationInline, IntakeAnswerInline]
