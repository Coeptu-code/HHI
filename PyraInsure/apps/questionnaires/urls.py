from django.urls import path

from . import views


urlpatterns = [
    path("questionnaires/create/", views.create_questionnaire_link, name="create_questionnaire_link"),
    path("questionnaires/created/<int:link_id>/", views.link_created, name="questionnaire_link_created"),
    path("admin/intake-links/", views.admin_intake_links, name="admin_intake_links"),
    path("admin/intake-links/<int:link_id>/", views.admin_intake_link_detail, name="admin_intake_link_detail"),
    path("admin/intake-links/<int:link_id>/mark-sent/", views.admin_intake_link_mark_sent, name="admin_intake_link_mark_sent"),
]
