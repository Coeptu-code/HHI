from __future__ import annotations

import json

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, JsonResponse
from django.shortcuts import get_object_or_404

from apps.gap_scoring.models import ProductAvailability, RuleConfig, ScoringWeight, TalkingPointTemplate
from apps.intake.services.intake_analysis import DEFAULT_RULES, DEFAULT_TALKING_POINT_TEMPLATES


def _parse_json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


@login_required
def admin_rules(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        configs = RuleConfig.objects.order_by("rule_key")
        return JsonResponse(
            {
                "items": [
                    {
                        "rule_key": config.rule_key,
                        "title": config.title,
                        "description": config.description,
                        "category": config.category,
                        "enabled": config.enabled,
                        "severity": config.severity,
                        "points": config.points,
                        "config": config.config,
                        "updated_at": config.updated_at.isoformat(),
                    }
                    for config in configs
                ]
            }
        )
    return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)


@login_required
def admin_rule_detail(request: HttpRequest, rule_key: str) -> JsonResponse:
    if request.method != "PATCH":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    config = get_object_or_404(RuleConfig, rule_key=rule_key)
    body = _parse_json_body(request)
    fields = {"enabled", "severity", "points", "title", "description", "config"}
    changed: list[str] = []
    for field in fields:
        if field not in body:
            continue
        value = body[field]
        if field == "points":
            value = int(value)
        setattr(config, field, value)
        changed.append(field)
    if changed:
        config.save(update_fields=changed + ["updated_at"])
    return JsonResponse({"ok": True, "rule_key": config.rule_key})


@login_required
def admin_rules_reset_defaults(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    for rule_key, rule in DEFAULT_RULES.items():
        RuleConfig.objects.update_or_create(
            rule_key=rule_key,
            defaults={
                "title": rule["title"],
                "description": "",
                "category": rule["category"],
                "enabled": True,
                "severity": rule["severity"],
                "points": rule["points"],
                "config": {},
            },
        )
    return JsonResponse({"ok": True})


@login_required
def admin_scoring_weights(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        return JsonResponse(
            {
                "items": [
                    {
                        "weight_key": weight.weight_key,
                        "label": weight.label,
                        "value": float(weight.value),
                        "enabled": weight.enabled,
                        "updated_at": weight.updated_at.isoformat(),
                    }
                    for weight in ScoringWeight.objects.order_by("weight_key")
                ]
            }
        )
    return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)


@login_required
def admin_scoring_weight_detail(request: HttpRequest, weight_key: str) -> JsonResponse:
    if request.method != "PATCH":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    weight = get_object_or_404(ScoringWeight, weight_key=weight_key)
    body = _parse_json_body(request)
    changed: list[str] = []
    if "label" in body:
        weight.label = str(body["label"])
        changed.append("label")
    if "value" in body:
        weight.value = body["value"]
        changed.append("value")
    if "enabled" in body:
        weight.enabled = bool(body["enabled"])
        changed.append("enabled")
    if changed:
        weight.save(update_fields=changed + ["updated_at"])
    return JsonResponse({"ok": True, "weight_key": weight.weight_key})


@login_required
def admin_talking_point_templates(request: HttpRequest) -> JsonResponse:
    if request.method == "GET":
        items = TalkingPointTemplate.objects.order_by("template_key")
        return JsonResponse(
            {
                "items": [
                    {
                        "template_key": item.template_key,
                        "finding_type": item.finding_type,
                        "title": item.title,
                        "category": item.category,
                        "hook": item.hook,
                        "suggested_script": item.suggested_script,
                        "quick_facts_template": item.quick_facts_template,
                        "enabled": item.enabled,
                    }
                    for item in items
                ]
            }
        )
    return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)


@login_required
def admin_talking_point_template_detail(request: HttpRequest, template_key: str) -> JsonResponse:
    if request.method != "PATCH":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    template = get_object_or_404(TalkingPointTemplate, template_key=template_key)
    body = _parse_json_body(request)
    fields = {"enabled", "title", "category", "hook", "suggested_script", "quick_facts_template", "finding_type"}
    changed: list[str] = []
    for field in fields:
        if field not in body:
            continue
        setattr(template, field, body[field])
        changed.append(field)
    if changed:
        template.save(update_fields=changed + ["updated_at"])
    return JsonResponse({"ok": True, "template_key": template.template_key})


@login_required
def admin_talking_point_templates_reset_defaults(request: HttpRequest) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    for finding_type, template in DEFAULT_TALKING_POINT_TEMPLATES.items():
        title, category, hook, script = template
        TalkingPointTemplate.objects.update_or_create(
            template_key=finding_type,
            defaults={
                "finding_type": finding_type,
                "title": title,
                "category": category,
                "hook": hook,
                "suggested_script": script,
                "quick_facts_template": [],
                "enabled": True,
            },
        )
    return JsonResponse({"ok": True})


@login_required
def admin_product_availability(request: HttpRequest) -> JsonResponse:
    if request.method == "POST":
        body = _parse_json_body(request)
        item = ProductAvailability.objects.create(
            state=str(body.get("state") or "").upper()[:2],
            coverage_type=str(body.get("coverage_type") or ""),
            carrier=str(body.get("carrier") or ""),
            product_name=str(body.get("product_name") or ""),
            status=str(body.get("status") or "available"),
            notes=str(body.get("notes") or ""),
        )
        return JsonResponse({"ok": True, "id": item.id}, status=201)

    queryset = ProductAvailability.objects.order_by("state", "coverage_type", "carrier")
    for field in ("state", "coverage_type", "carrier", "status"):
        value = request.GET.get(field)
        if value:
            queryset = queryset.filter(**{field: value})
    return JsonResponse(
        {
            "items": [
                {
                    "id": item.id,
                    "state": item.state,
                    "coverage_type": item.coverage_type,
                    "carrier": item.carrier,
                    "product_name": item.product_name,
                    "status": item.status,
                    "notes": item.notes or None,
                    "created_at": item.created_at.isoformat(),
                    "updated_at": item.updated_at.isoformat(),
                }
                for item in queryset
            ]
        }
    )


@login_required
def admin_product_availability_detail(request: HttpRequest, item_id: int) -> JsonResponse:
    item = get_object_or_404(ProductAvailability, id=item_id)
    if request.method == "DELETE":
        item.delete()
        return JsonResponse({"ok": True})
    if request.method != "PATCH":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    body = _parse_json_body(request)
    fields = {"state", "coverage_type", "carrier", "product_name", "status", "notes"}
    changed: list[str] = []
    for field in fields:
        if field not in body:
            continue
        value = body[field]
        if field == "state":
            value = str(value).upper()[:2]
        setattr(item, field, value)
        changed.append(field)
    if changed:
        item.save(update_fields=changed + ["updated_at"])
    return JsonResponse({"ok": True, "id": item.id})
