from django.urls import path

from . import views


urlpatterns = [
    path("admin/rules/", views.admin_rules, name="admin_rules"),
    path("admin/rules/<str:rule_key>/", views.admin_rule_detail, name="admin_rule_detail"),
    path("admin/rules/reset-defaults/", views.admin_rules_reset_defaults, name="admin_rules_reset_defaults"),
    path("admin/scoring-weights/", views.admin_scoring_weights, name="admin_scoring_weights"),
    path("admin/scoring-weights/<str:weight_key>/", views.admin_scoring_weight_detail, name="admin_scoring_weight_detail"),
    path(
        "admin/talking-point-templates/",
        views.admin_talking_point_templates,
        name="admin_talking_point_templates",
    ),
    path(
        "admin/talking-point-templates/<str:template_key>/",
        views.admin_talking_point_template_detail,
        name="admin_talking_point_template_detail",
    ),
    path(
        "admin/talking-point-templates/reset-defaults/",
        views.admin_talking_point_templates_reset_defaults,
        name="admin_talking_point_templates_reset_defaults",
    ),
    path("admin/product-availability/", views.admin_product_availability, name="admin_product_availability"),
    path(
        "admin/product-availability/<int:item_id>/",
        views.admin_product_availability_detail,
        name="admin_product_availability_detail",
    ),
]
