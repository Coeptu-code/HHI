from django.contrib import admin

from .models import CustomerRecord


@admin.register(CustomerRecord)
class CustomerRecordAdmin(admin.ModelAdmin):
    list_display = ("id", "agent", "first_name", "last_name", "email", "phone", "state", "created_at")
    search_fields = ("first_name", "last_name", "email", "phone")

# Register your models here.
