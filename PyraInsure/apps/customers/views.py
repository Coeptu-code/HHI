from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.customers.models import CustomerRecord
from apps.intake.models import IntakeSubmission


@login_required
def customer_detail(request, customer_id: int):
    customer = get_object_or_404(CustomerRecord, id=customer_id)
    submissions = (
        IntakeSubmission.objects.filter(customer=customer)
        .select_related("questionnaire_link")
        .order_by("-created_at")
    )
    return render(request, "customers/detail.html", {"customer": customer, "submissions": submissions})
