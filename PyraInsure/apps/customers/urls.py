from django.urls import path

from . import views


urlpatterns = [
    path("customers/", views.customer_list, name="customer_list"),
    path("customers/<int:customer_id>/", views.customer_detail, name="customer_detail"),
    path("customers/<int:customer_id>/activity/", views.customer_activity, name="customer_activity"),
    path("customers/<int:customer_id>/assignment/", views.customer_assignment_update, name="customer_assignment_update"),
    path("customers/<int:customer_id>/findings/", views.customer_findings, name="customer_findings"),
    path("customers/<int:customer_id>/findings/<int:finding_id>/", views.customer_finding_detail, name="customer_finding_detail"),
    path("customers/<int:customer_id>/notes/", views.customer_notes, name="customer_notes"),
    path("customers/<int:customer_id>/notes/<int:note_id>/", views.customer_note_detail, name="customer_note_detail"),
    path("customers/<int:customer_id>/pre-call-summary/", views.customer_pre_call_summary, name="customer_pre_call_summary"),
    path(
        "customers/<int:customer_id>/pre-call-summary/regenerate/",
        views.customer_pre_call_summary_regenerate,
        name="customer_pre_call_summary_regenerate",
    ),
]
