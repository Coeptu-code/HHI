from django.urls import path

from . import views


urlpatterns = [
    path("questionnaires/create/", views.create_questionnaire_link, name="create_questionnaire_link"),
    path("questionnaires/created/<int:link_id>/", views.link_created, name="questionnaire_link_created"),
]
