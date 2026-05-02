from django.urls import path

from . import views


urlpatterns = [
    path("drugs/search/", views.drug_search, name="drug_search"),
    path("intake/thank-you/", views.intake_thank_you, name="intake_thank_you"),
    path("intake/thank-you/<str:score_token>/", views.intake_thank_you, name="intake_thank_you"),
    path("score/<str:score_token>/", views.coveragap_score_view, name="coveragap_score"),
    path("intake/<str:token>/", views.intake_entry, name="intake_entry"),
    path("intake/<str:token>/chat/", views.intake_messenger, name="intake_messenger"),
    path("intake/<str:token>/chat/api/", views.intake_messenger_api, name="intake_messenger_api"),
    path("intake/<str:token>/step/<str:step>/", views.intake_step, name="intake_step"),
    path("intake/<str:token>/household/add-spouse/", views.intake_household_add_spouse, name="intake_household_add_spouse"),
    path("intake/<str:token>/household/add-dependent/", views.intake_household_add_dependent, name="intake_household_add_dependent"),
    path("intake/<str:token>/household/<str:member_id>/edit/", views.intake_household_edit, name="intake_household_edit"),
    path("intake/<str:token>/household/<str:member_id>/delete/", views.intake_household_delete, name="intake_household_delete"),
    path("intake/<str:token>/submit/", views.intake_submit, name="intake_submit"),
    path("summaries/<int:submission_id>/", views.pre_call_summary, name="pre_call_summary"),
    path("intake-sessions/<int:submission_id>/analyze/", views.analyze_intake_session_admin, name="intake_session_analyze"),
    path("submissions/<int:submission_id>/analysis/", views.submission_analysis, name="submission_analysis"),
    path("admin/submissions/<int:submission_id>/review/", views.admin_submission_review, name="admin_submission_review"),
]
