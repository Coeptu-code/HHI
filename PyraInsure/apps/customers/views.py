from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from apps.agents.models import AgentProfile
from apps.customers.models import AgentNote, CustomerRecord
from apps.customers.services import (
    build_customer_detail_payload,
    build_customer_list_payload,
    list_customer_activity,
    record_admin_event,
)
from apps.gap_scoring.models import GapFinding
from apps.intake.models import IntakeSubmission
from apps.intake.services import build_pre_call_summary
import json


def _wants_json(request: HttpRequest) -> bool:
    fmt = request.GET.get("format", "").strip().lower()
    if fmt == "json":
        return True
    accept = request.headers.get("Accept", "").lower()
    return "application/json" in accept


def _parse_int(value: str | None, default: int = 0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _parse_json_body(request: HttpRequest) -> dict:
    if not request.body:
        return {}
    try:
        return json.loads(request.body.decode("utf-8"))
    except Exception:
        return {}


def _get_customer_for_user(request: HttpRequest, customer_id: int) -> CustomerRecord:
    if request.user.is_staff:
        return get_object_or_404(CustomerRecord, id=customer_id)
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)
    return get_object_or_404(CustomerRecord, id=customer_id, agent=agent_profile)


@login_required
def customer_list(request: HttpRequest) -> HttpResponse:
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)
    base_queryset = CustomerRecord.objects.filter(agent=agent_profile).select_related("agent", "agent__user")
    assigned_agent_id = _parse_int(request.GET.get("assigned_agent_id"), default=0)
    if assigned_agent_id:
        if request.user.is_staff:
            base_queryset = CustomerRecord.objects.filter(agent_id=assigned_agent_id).select_related("agent", "agent__user")
        elif assigned_agent_id == agent_profile.id:
            base_queryset = base_queryset.filter(agent_id=assigned_agent_id)

    if _wants_json(request):
        payload = build_customer_list_payload(
            base_queryset=base_queryset.order_by("-created_at"),
            params={key: value for key, value in request.GET.items()},
        )
        return JsonResponse(payload)

    customers = base_queryset.order_by("-created_at")
    return render(request, "customers/list.html", {
        "customers": customers,
        "customer_rows": build_customer_list_payload(
            base_queryset=customers,
            params={},
        )["results"],
        "active_nav": "customers",
    })


@login_required
def customer_detail(request: HttpRequest, customer_id: int) -> HttpResponse:
    customer = _get_customer_for_user(request, customer_id)
    record_admin_event(
        customer_id=customer.id,
        intake_session_id=None,
        activity_type="customer_viewed",
        title="Customer profile viewed",
        actor_name=request.user.get_username(),
        dedupe_window_seconds=600,
    )

    if _wants_json(request):
        return JsonResponse(build_customer_detail_payload(customer))

    submissions = (
        IntakeSubmission.objects.filter(customer=customer)
        .select_related("questionnaire_link")
        .order_by("-created_at")
    )
    return render(request, "customers/detail.html", {
        "customer": customer,
        "submissions": submissions,
        "active_nav": "customers",
    })


@login_required
def customer_pre_call_summary(request: HttpRequest, customer_id: int) -> JsonResponse:
    customer = _get_customer_for_user(request, customer_id)
    session_id = _parse_int(request.GET.get("intake_session_id"), default=0) or None
    payload = build_pre_call_summary(customer.id, intake_session_id=session_id)
    record_admin_event(
        customer_id=customer.id,
        intake_session_id=session_id,
        activity_type="pre_call_summary_opened",
        title="Pre-call summary opened",
        actor_name=request.user.get_username(),
        dedupe_window_seconds=120,
    )
    return JsonResponse(payload)


@login_required
def customer_pre_call_summary_regenerate(request: HttpRequest, customer_id: int) -> JsonResponse:
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)

    customer = _get_customer_for_user(request, customer_id)
    session_id = _parse_int(request.GET.get("intake_session_id"), default=0) or None
    payload = build_pre_call_summary(customer.id, intake_session_id=session_id)
    record_admin_event(
        customer_id=customer.id,
        intake_session_id=session_id,
        activity_type="pre_call_summary_regenerated",
        title="Pre-call summary regenerated",
        actor_name=request.user.get_username(),
    )
    payload["ok"] = True
    return JsonResponse(payload)


@login_required
def customer_activity(request: HttpRequest, customer_id: int) -> JsonResponse:
    customer = _get_customer_for_user(request, customer_id)
    limit = _parse_int(request.GET.get("limit"), default=25)
    offset = _parse_int(request.GET.get("offset"), default=0)
    activity_type = request.GET.get("activity_type") or None
    payload = list_customer_activity(customer_id=customer.id, limit=limit, offset=offset, activity_type=activity_type)
    return JsonResponse(payload)


@login_required
def customer_assignment_update(request: HttpRequest, customer_id: int) -> JsonResponse:
    if request.method != "PATCH":
        return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
    customer = _get_customer_for_user(request, customer_id)
    body = _parse_json_body(request)
    assigned_agent_id = body.get("assigned_agent_id")
    assigned_agent_name = body.get("assigned_agent_name")

    if assigned_agent_id:
        try:
            new_agent = AgentProfile.objects.get(id=int(assigned_agent_id))
        except Exception:
            return JsonResponse({"ok": False, "error": "Assigned agent not found."}, status=404)
        customer.agent = new_agent
        customer.save(update_fields=["agent", "updated_at"])
    elif assigned_agent_name:
        new_agent = (
            AgentProfile.objects.filter(
                Q(user__username__iexact=str(assigned_agent_name).strip())
                | Q(user__first_name__iexact=str(assigned_agent_name).strip())
                | Q(user__last_name__iexact=str(assigned_agent_name).strip())
            )
            .first()
        )
        if new_agent is None:
            return JsonResponse({"ok": False, "error": "assigned_agent_name could not be resolved."}, status=400)
        customer.agent = new_agent
        customer.save(update_fields=["agent", "updated_at"])
    else:
        return JsonResponse({"ok": False, "error": "Provide assigned_agent_id or assigned_agent_name."}, status=400)

    record_admin_event(
        customer_id=customer.id,
        intake_session_id=None,
        activity_type="agent_assignment_updated",
        title="Agent assignment updated",
        actor_name=request.user.get_username(),
        metadata={"assigned_agent_id": customer.agent_id},
    )
    return JsonResponse({"ok": True, "customer_id": customer.id, "assigned_agent_id": customer.agent_id, "assigned_agent_name": customer.assigned_agent_name})


@login_required
def customer_findings(request: HttpRequest, customer_id: int) -> JsonResponse:
    customer = _get_customer_for_user(request, customer_id)
    if request.method == "POST":
        body = _parse_json_body(request)
        finding = GapFinding.objects.create(
            customer=customer,
            submission_id=body.get("intake_session_id"),
            finding_type=str(body.get("finding_type") or "manual"),
            category=str(body.get("category") or "health"),
            title=str(body.get("title") or "Manual finding"),
            severity=str(body.get("severity") or "medium"),
            points=int(body.get("points") or 0),
            explanation=str(body.get("explanation") or ""),
            description=str(body.get("explanation") or ""),
            status=str(body.get("status") or "open"),
            assigned_to=str(body.get("assigned_to") or "hutchins"),
            is_generated=False,
        )
        record_admin_event(
            customer_id=customer.id,
            intake_session_id=finding.submission_id,
            activity_type="finding_created",
            title="Manual finding created",
            actor_name=request.user.get_username(),
            metadata={"finding_id": finding.id},
        )
        return JsonResponse({"ok": True, "finding_id": finding.id}, status=201)

    findings = GapFinding.objects.filter(customer=customer).order_by("-created_at")
    return JsonResponse(
        {
            "items": [
                {
                    "id": finding.id,
                    "finding_type": finding.finding_type,
                    "title": finding.title,
                    "severity": finding.severity,
                    "points": finding.points,
                    "explanation": finding.explanation or finding.description,
                    "status": finding.status,
                    "is_generated": finding.is_generated,
                    "created_at": finding.created_at.isoformat(),
                }
                for finding in findings
            ]
        }
    )


@login_required
def customer_finding_detail(request: HttpRequest, customer_id: int, finding_id: int) -> JsonResponse:
    customer = _get_customer_for_user(request, customer_id)
    finding = get_object_or_404(GapFinding, id=finding_id, customer=customer)

    if request.method == "PATCH":
        body = _parse_json_body(request)
        updatable_fields = {"title", "severity", "points", "explanation", "status", "assigned_to"}
        for field in updatable_fields:
            if field not in body:
                continue
            value = body[field]
            if field == "points":
                value = int(value)
            setattr(finding, field, value)
        if "explanation" in body:
            finding.description = str(body.get("explanation") or "")
        finding.save()

        if finding.status == "dismissed":
            activity_type = "finding_dismissed"
            title = "Finding dismissed"
        elif finding.status == "resolved":
            activity_type = "finding_resolved"
            title = "Finding resolved"
        else:
            activity_type = "finding_created"
            title = "Finding updated"
        record_admin_event(
            customer_id=customer.id,
            intake_session_id=finding.submission_id,
            activity_type=activity_type,
            title=title,
            actor_name=request.user.get_username(),
            metadata={"finding_id": finding.id},
        )
        return JsonResponse({"ok": True, "finding_id": finding.id})

    if request.method == "DELETE":
        finding.status = "dismissed"
        finding.save(update_fields=["status", "updated_at"])
        record_admin_event(
            customer_id=customer.id,
            intake_session_id=finding.submission_id,
            activity_type="finding_dismissed",
            title="Finding dismissed",
            actor_name=request.user.get_username(),
            metadata={"finding_id": finding.id},
        )
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)


@login_required
def customer_notes(request: HttpRequest, customer_id: int) -> JsonResponse:
    customer = _get_customer_for_user(request, customer_id)
    if request.method == "POST":
        body = _parse_json_body(request)
        note = AgentNote.objects.create(
            customer=customer,
            intake_session_id=body.get("intake_session_id"),
            note=str(body.get("note") or ""),
            note_type=str(body.get("note_type") or "general"),
            created_by=request.user,
        )
        record_admin_event(
            customer_id=customer.id,
            intake_session_id=note.intake_session_id,
            activity_type="agent_note_added",
            title="Agent note added",
            actor_name=request.user.get_username(),
            metadata={"note_id": note.id},
        )
        return JsonResponse({"ok": True, "note_id": note.id}, status=201)

    notes = AgentNote.objects.filter(customer=customer).order_by("-created_at")
    return JsonResponse(
        {
            "items": [
                {
                    "id": note.id,
                    "note": note.note,
                    "note_type": note.note_type,
                    "created_by": note.created_by.get_username() if note.created_by else None,
                    "created_at": note.created_at.isoformat(),
                    "updated_at": note.updated_at.isoformat(),
                }
                for note in notes
            ]
        }
    )


@login_required
def customer_note_detail(request: HttpRequest, customer_id: int, note_id: int) -> JsonResponse:
    customer = _get_customer_for_user(request, customer_id)
    note = get_object_or_404(AgentNote, id=note_id, customer=customer)

    if request.method == "PATCH":
        body = _parse_json_body(request)
        if "note" in body:
            note.note = str(body["note"])
        if "note_type" in body:
            note.note_type = str(body["note_type"])
        note.save()
        record_admin_event(
            customer_id=customer.id,
            intake_session_id=note.intake_session_id,
            activity_type="agent_note_updated",
            title="Agent note updated",
            actor_name=request.user.get_username(),
            metadata={"note_id": note.id},
        )
        return JsonResponse({"ok": True, "note_id": note.id})

    if request.method == "DELETE":
        note.delete()
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "error": "Method not allowed."}, status=405)
