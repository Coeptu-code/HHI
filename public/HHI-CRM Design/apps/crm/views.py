from __future__ import annotations

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST
from django.views.generic import TemplateView

from .forms import ClientAttachmentUploadForm, ClientIntakeForm, DocumentUploadForm
from .models import Client, ClientAttachment, ClientAttachmentPage, HandwrittenNote, PolicyDocument
from .services.dashboard_service import clients_added_last_n_days, clients_turning_65
from .services.policy_pdf_service import is_image
from .services.document_service import create_policy_document
from .services.normalizers import lookup_zip, normalize_phone_number


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard/index.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.setdefault("page_title", "Dashboard")
        ctx.setdefault("active_page", "dashboard")

        added = clients_added_last_n_days(days=7)
        turning = clients_turning_65(window_days=90)

        ctx["clients_added_7_days"] = added
        ctx["clients_turning_65"] = turning

        ctx["dashboard_cards"] = [
            {
                "key": "clients_added_7_days",
                "title": "Clients Added",
                "subtitle": "Last 7 days (incl. today)",
                "metric": str(added["total"]),
                "body_template": "dashboard/cards/clients_added_7_days.html",
                "action_label": "View clients",
                "action_url_name": "crm:client-list",
            },
            {
                "key": "turning_65",
                "title": "Clients Turning 65",
                "subtitle": "Next 90 days",
                "metric": str(len(turning)),
                "body_template": "dashboard/cards/clients_turning_65.html",
                "action_label": "Client list",
                "action_url_name": "crm:client-list",
            },
            {
                "key": "quick_actions",
                "title": "Quick Actions",
                "subtitle": "Common CRM tasks",
                "metric": "",
                "body_template": "dashboard/cards/quick_actions.html",
            },
        ]

        return ctx

@require_http_methods(["GET", "POST"])
@login_required
def document_upload_view(request):
    result = None

    if request.method == "POST":
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            client = form.cleaned_data.get("client")
            document_type = form.cleaned_data["document_type"]
            single_file = form.cleaned_data.get("file")
            multi_files = request.FILES.getlist("files")
            notes = form.cleaned_data.get("notes", "")

            try:
                if document_type == "handwritten_note":
                    if not single_file:
                        form.add_error("file", "Please upload one handwritten note file.")
                    else:
                        note = HandwrittenNote.objects.create(
                            client=client,
                            uploaded_file=single_file,
                            original_filename=getattr(single_file, "name", ""),
                            notes=notes,
                        )
                        return redirect("crm:handwritten-note-review", note_id=note.id)

                elif document_type == "policy":
                    policy = create_policy_document(
                        client,
                        single_file=single_file,
                        multiple_files=multi_files,
                        notes=notes,
                    )
                    result = {
                        "type": "policy",
                        "id": policy.id,
                        "file_url": policy.file.url if policy.file else "",
                        "page_count": policy.page_count,
                    }

            except Exception as exc:
                form.add_error(None, str(exc))
    else:
        form = DocumentUploadForm()

    return render(
        request,
        "crm/document_upload.html",
        {
            "form": form,
            "result": result,
            "page_title": "Document Upload",
            "active_page": "client_list",
        },
    )


@require_http_methods(["GET", "POST"])
@login_required
def handwritten_note_review_view(request, note_id: int):
    note = get_object_or_404(HandwrittenNote, pk=note_id)
    if request.method == "POST":
        note.notes = (request.POST.get("notes") or "").strip()
        note.save(update_fields=["notes"])
        messages.success(request, "Handwritten note updated.")
        return redirect("crm:handwritten-note-review", note_id=note.id)

    return render(
        request,
        "crm/handwritten_note_review.html",
        {
            "note": note,
            "page_title": f"Handwritten Note #{note.id}",
            "active_page": "client_list",
        },
    )

@require_http_methods(["GET"])
@login_required
def policy_detail_view(request, pk: int):
    policy = PolicyDocument.objects.get(pk=pk)
    return render(
        request,
        "crm/policy_detail.html",
        {
            "policy": policy,
            "page_title": f"Policy #{policy.id}",
            "active_page": "client_list",
        },
    )


@require_http_methods(["GET", "POST"])
@login_required
def client_intake_view(request, client_id: int | None = None):
    client = Client.objects.filter(pk=client_id).first() if client_id else None
    page_title = "Edit Client" if client else "New Client Intake"

    if request.method == "POST":
        form = ClientIntakeForm(request.POST, request.FILES, instance=client)
        if form.is_valid():
            client = form.save(commit=False)
            client.phone_number = normalize_phone_number(form.cleaned_data.get("phone_number", ""))
            client.save()

            policy_pdf = form.cleaned_data.get("policy_pdf")
            policy_images = request.FILES.getlist("policy_images")
            policy_notes = (form.cleaned_data.get("policy_notes") or "").strip()
            handwritten_file = form.cleaned_data.get("handwritten_note_file")
            handwritten_notes = (form.cleaned_data.get("handwritten_note_notes") or "").strip()

            try:
                if policy_pdf:
                    create_policy_document(client, single_file=policy_pdf, notes=policy_notes)
                elif policy_images:
                    create_policy_document(client, multiple_files=policy_images, notes=policy_notes)
            except Exception as exc:
                form.add_error(None, str(exc))
                return render(
                    request,
                    "crm/client_intake_form.html",
                    {
                        "form": form,
                        "client": client,
                        "page_title": page_title,
                        "active_page": "client_intake",
                    },
                )

            if handwritten_file:
                HandwrittenNote.objects.create(
                    client=client,
                    uploaded_file=handwritten_file,
                    original_filename=getattr(handwritten_file, "name", ""),
                    notes=handwritten_notes,
                )

            messages.success(request, "Client intake saved.")
            return redirect("crm:client-detail", client_id=client.id)
    else:
        form = ClientIntakeForm(instance=client)

    return render(
        request,
        "crm/client_intake_form.html",
        {
            "form": form,
            "client": client,
            "page_title": page_title,
            "active_page": "client_intake",
        },
    )


@require_http_methods(["GET"])
@login_required
def client_detail_view(request, client_id: int):
    client = get_object_or_404(
        Client.objects.prefetch_related("attachments__pages", "policy_documents", "handwritten_notes"),
        pk=client_id,
    )

    attachments_data: list[dict] = []
    for attachment in client.attachments.all():
        pages = [
            {
                "page_number": page.page_number,
                "url": page.image.url if page.image else "",
                "original_filename": page.original_filename or "",
                "created_at": page.created_at.isoformat() if page.created_at else "",
            }
            for page in attachment.pages.all()
        ]

        attachments_data.append(
            {
                "id": attachment.id,
                "display_name": attachment.display_name or "Attachment",
                "document_type": attachment.document_type,
                "document_type_label": attachment.get_document_type_display(),
                "page_count": int(attachment.page_count or len(pages)),
                "created_at": attachment.created_at.isoformat() if attachment.created_at else "",
                "created_at_display": attachment.created_at.strftime("%m/%d/%Y %I:%M %p") if attachment.created_at else "",
                "first_page_url": (pages[0]["url"] if pages else ""),
                "pages": pages,
            }
        )
    return render(
        request,
        "crm/client_detail.html",
        {
            "client": client,
            "attachment_form": ClientAttachmentUploadForm(),
            "attachments_data": attachments_data,
            "page_title": client.full_name,
            "active_page": "client_list",
        },
    )


@require_http_methods(["GET"])
@login_required
def client_scan_view(request, client_id: int):
    client = get_object_or_404(Client, pk=client_id)
    return render(
        request,
        "crm/client_scan_page.html",
        {
            "client": client,
            "attachment_form": ClientAttachmentUploadForm(),
            "page_title": "Scan Document",
            "active_page": "client_list",
        },
    )


@require_http_methods(["GET"])
@login_required
def client_list_view(request):
    query = (request.GET.get("q") or "").strip()

    clients = Client.objects.all()
    if query:
        clients = clients.filter(
            Q(full_name__icontains=query) | Q(phone_number__icontains=query) | Q(email__icontains=query)
        )

    clients = clients.order_by("-created_at")
    paginator = Paginator(clients, 25)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "crm/client_list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "page_title": "Client List",
            "active_page": "client_list",
        },
    )


@require_http_methods(["GET"])
@login_required
def zip_lookup_view(request):
    zip_code = request.GET.get("zip", "")
    result = lookup_zip(zip_code)
    if not result:
        return JsonResponse({"ok": False, "error": "ZIP not found."}, status=404)
    return JsonResponse({"ok": True, **result})


@require_POST
@login_required
def client_attachment_upload_view(request, client_id: int):
    client = get_object_or_404(Client, pk=client_id)
    form = ClientAttachmentUploadForm(request.POST)

    if not form.is_valid():
        return JsonResponse({"ok": False, "error": form.errors.get_json_data()}, status=400)

    files = request.FILES.getlist("pages")
    if not files:
        return JsonResponse({"ok": False, "error": "No page images were uploaded."}, status=400)

    if any(not is_image(f) for f in files):
        return JsonResponse({"ok": False, "error": "All uploaded pages must be image files."}, status=400)

    document_type = form.cleaned_data["document_type"]
    display_name = (form.cleaned_data.get("display_name") or "").strip()
    if not display_name:
        display_name = f"{document_type.replace('_', ' ').title()} Upload"

    with transaction.atomic():
        attachment = ClientAttachment.objects.create(
            client=client,
            document_type=document_type,
            display_name=display_name,
            status=ClientAttachment.Status.UPLOADED,
            page_count=len(files),
        )

        for idx, file_obj in enumerate(files, start=1):
            ClientAttachmentPage.objects.create(
                attachment=attachment,
                page_number=idx,
                image=file_obj,
                original_filename=getattr(file_obj, "name", "") or "",
            )

    return JsonResponse(
        {
            "ok": True,
            "attachment_id": attachment.id,
            "page_count": attachment.page_count,
            "status": attachment.status,
        }
    )
