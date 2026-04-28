from django.urls import path

from .views import (
    DashboardView,
    client_attachment_upload_view,
    client_detail_view,
    client_list_view,
    client_scan_view,
    client_intake_view,
    document_upload_view,
    handwritten_note_review_view,
    policy_detail_view,
    zip_lookup_view,
)

app_name = "crm"

urlpatterns = [
    path("", DashboardView.as_view(), name="dashboard"),
    path("clients/", client_list_view, name="client-list"),
    path("clients/intake/", client_intake_view, name="client-intake"),
    path("clients/<int:client_id>/edit/", client_intake_view, name="client-edit"),
    path("clients/<int:client_id>/", client_detail_view, name="client-detail"),
    path("clients/<int:client_id>/scan/", client_scan_view, name="client-scan"),
    path(
        "clients/<int:client_id>/attachments/upload/",
        client_attachment_upload_view,
        name="client-attachment-upload",
    ),
    path("clients/zip-lookup/", zip_lookup_view, name="zip-lookup"),
    path("documents/upload/", document_upload_view, name="document-upload"),
    path(
        "documents/handwritten/<int:note_id>/review/",
        handwritten_note_review_view,
        name="handwritten-note-review",
    ),
    path("policies/<int:pk>/", policy_detail_view, name="policy-detail"),
]
