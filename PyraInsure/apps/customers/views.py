from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.agents.models import AgentProfile
from apps.customers.models import CustomerRecord
from apps.intake.models import IntakeSubmission


@login_required
def customer_list(request):
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)
    customers = CustomerRecord.objects.filter(agent=agent_profile).order_by("-created_at")
    return render(request, "customers/list.html", {
        "customers": customers,
        "active_nav": "customers",
    })


@login_required
def customer_detail(request, customer_id: int):
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)
    customer = get_object_or_404(CustomerRecord, id=customer_id, agent=agent_profile)
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
