from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from apps.agents.models import AgentProfile
from apps.customers.models import CustomerRecord
from apps.customers.services import record_admin_event
from apps.questionnaires.forms import QuestionnaireLinkCreateForm
from apps.questionnaires.models import QuestionnaireLink
import json


def _parse_json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def _normalize_module_order(raw_value: object, *, enabled: dict[str, bool]) -> list[str]:
    parsed = raw_value
    if isinstance(raw_value, str):
        try:
            parsed = json.loads(raw_value)
        except Exception:
            parsed = [item.strip() for item in raw_value.split(",") if item.strip()]
    if not isinstance(parsed, list):
        return []

    normalized: list[str] = []
    for item in parsed:
        module = str(item or "").strip().lower()
        if module not in QuestionnaireLink.MODULE_KEYS:
            continue
        if not enabled.get(module, False):
            continue
        if module in normalized:
            continue
        normalized.append(module)
    return normalized


def _normalize_phone(value: str) -> str:
    digits = "".join(ch for ch in str(value or "") if ch.isdigit())
    return digits


def _find_customer_by_phone(*, agent_profile: AgentProfile, phone: str) -> CustomerRecord | None:
    if not phone:
        return None
    normalized_input = _normalize_phone(phone)
    if not normalized_input:
        return None

    direct_match = CustomerRecord.objects.filter(agent=agent_profile, phone=phone).first()
    if direct_match:
        return direct_match

    for customer in CustomerRecord.objects.filter(agent=agent_profile).exclude(phone=""):
        if _normalize_phone(customer.phone) == normalized_input:
            return customer
    return None


@login_required
def create_questionnaire_link(request: HttpRequest) -> HttpResponse:
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = QuestionnaireLinkCreateForm(request.POST)
        if form.is_valid():
            full_name = str(form.cleaned_data.get("client_name") or "").strip()
            phone = str(form.cleaned_data.get("phone") or "").strip()
            customer: CustomerRecord | None = _find_customer_by_phone(agent_profile=agent_profile, phone=phone)
            if customer is None and (full_name or phone):
                if full_name:
                    first_name, _, last_name = full_name.partition(" ")
                else:
                    first_name, last_name = "Client", ""
                customer = CustomerRecord.objects.create(
                    agent=agent_profile,
                    first_name=first_name.strip() or "Client",
                    last_name=last_name.strip(),
                    email="",
                    phone=phone,
                    state="",
                    preferred_contact_method="",
                )

            link: QuestionnaireLink = form.save(commit=False)
            link.agent = agent_profile
            link.customer = customer
            link.created_by = request.user
            link.status = "created"
            link.delivery_method = None
            link.module_order = form.cleaned_data.get("module_order") or []
            link.save()
            record_admin_event(
                customer_id=link.customer_id,
                intake_session_id=None,
                activity_type="intake_link_created",
                title="Intake link created",
                actor_name=request.user.get_username(),
                metadata={"link_id": link.id},
            )
            return redirect("questionnaire_link_created", link_id=link.id)
    else:
        form = QuestionnaireLinkCreateForm(
            initial={
                "include_health": True,
                "include_life": True,
                "include_auto": True,
                "include_home": True,
                "include_umbrella": True,
                "module_order": json.dumps(["health", "life", "auto", "home", "umbrella"]),
            }
        )

    return render(request, "questionnaires/create_link.html", {"form": form, "active_nav": "links"})


@login_required
def link_created(request: HttpRequest, link_id: int) -> HttpResponse:
    link = get_object_or_404(QuestionnaireLink, id=link_id, agent__user=request.user)
    intake_url = request.build_absolute_uri(reverse("intake_entry", args=[link.token]))
    return render(request, "questionnaires/link_created.html", {"link": link, "intake_url": intake_url, "active_nav": "links"})


@login_required
def admin_intake_links(request: HttpRequest) -> JsonResponse:
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)
    if request.method == "POST":
        body = _parse_json_body(request)
        enabled = {
            "health": bool(body.get("include_health", True)),
            "life": bool(body.get("include_life", True)),
            "auto": bool(body.get("include_auto", True)),
            "home": bool(body.get("include_home", True)),
            "umbrella": bool(body.get("include_umbrella", True)),
        }
        link = QuestionnaireLink.objects.create(
            agent=agent_profile,
            customer_id=body.get("customer_id"),
            created_by=request.user,
            include_health=enabled["health"],
            include_life=enabled["life"],
            include_auto=enabled["auto"],
            include_home=enabled["home"],
            include_umbrella=enabled["umbrella"],
            delivery_method=body.get("delivery_method"),
            module_order=_normalize_module_order(body.get("module_order"), enabled=enabled),
            status="created",
        )
        record_admin_event(
            customer_id=link.customer_id,
            intake_session_id=None,
            activity_type="intake_link_created",
            title="Intake link created",
            actor_name=request.user.get_username(),
            metadata={"link_id": link.id},
        )
        return JsonResponse({"ok": True, "id": link.id, "token": link.token}, status=201)

    queryset = QuestionnaireLink.objects.filter(agent=agent_profile).order_by("-created_at")
    status = request.GET.get("status")
    if status:
        queryset = queryset.filter(status=status)
    customer_id = request.GET.get("customer_id")
    if customer_id:
        queryset = queryset.filter(customer_id=customer_id)
    items = [
        {
            "id": link.id,
            "token": link.token,
            "customer_id": link.customer_id,
            "status": link.status,
            "delivery_method": link.delivery_method,
            "module_order": link.module_order or [],
            "sent_at": link.sent_at.isoformat() if link.sent_at else None,
            "started_at": link.started_at.isoformat() if link.started_at else None,
            "submitted_at": link.completed_at.isoformat() if link.completed_at else None,
            "last_opened_at": link.last_opened_at.isoformat() if link.last_opened_at else None,
            "open_count": link.open_count,
            "created_at": link.created_at.isoformat(),
        }
        for link in queryset
    ]
    return JsonResponse({"items": items})


@login_required
def admin_intake_link_detail(request: HttpRequest, link_id: int) -> JsonResponse:
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)
    link = get_object_or_404(QuestionnaireLink, id=link_id, agent=agent_profile)
    if request.method != "PATCH":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    body = _parse_json_body(request)
    updatable = {"status", "delivery_method", "customer_id", "is_active", "expires_at", "module_order"}
    changed_fields: list[str] = []
    for field in updatable:
        if field not in body:
            continue
        if field == "module_order":
            enabled = {
                "health": link.include_health,
                "life": link.include_life,
                "auto": link.include_auto,
                "home": link.include_home,
                "umbrella": link.include_umbrella,
            }
            setattr(link, field, _normalize_module_order(body[field], enabled=enabled))
        else:
            setattr(link, field, body[field])
        changed_fields.append(field)
    if changed_fields:
        link.save()
    return JsonResponse({"ok": True, "id": link.id})


@login_required
def admin_intake_link_mark_sent(request: HttpRequest, link_id: int) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)
    link = get_object_or_404(QuestionnaireLink, id=link_id, agent=agent_profile)
    body = _parse_json_body(request)
    link.sent_at = timezone.now()
    link.status = "sent"
    if body.get("delivery_method"):
        link.delivery_method = str(body.get("delivery_method"))
    link.save(update_fields=["sent_at", "status", "delivery_method"])
    record_admin_event(
        customer_id=link.customer_id,
        intake_session_id=None,
        activity_type="intake_link_sent",
        title="Intake link sent",
        actor_name=request.user.get_username(),
        metadata={"link_id": link.id, "delivery_method": link.delivery_method},
    )
    return JsonResponse({"ok": True, "id": link.id})
