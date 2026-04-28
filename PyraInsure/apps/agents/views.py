from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.shortcuts import render
from django.urls import reverse

from apps.agents.models import AgentProfile
from apps.gap_scoring.models import GapFinding
from apps.intake.models import IntakeSubmission
from apps.questionnaires.models import QuestionnaireLink
from apps.referrals.models import ReferralOpportunity


@login_required
def dashboard(request):
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)

    submissions = (
        IntakeSubmission.objects.filter(agent=agent_profile)
        .select_related("customer")
        .order_by("-created_at")
    )
    total_submissions = submissions.count()
    recent_submissions = submissions[:10]

    referral_count = ReferralOpportunity.objects.filter(submission__agent=agent_profile).count()

    recent_links_qs = QuestionnaireLink.objects.filter(agent=agent_profile).order_by("-created_at")[:10]
    recent_links = []
    for link in recent_links_qs:
        recent_links.append(
            {
                "link": link,
                "intake_url": request.build_absolute_uri(reverse("intake_entry", args=[link.token])),
            }
        )

    # Coverage score is computed from findings; show a lightweight placeholder-friendly value.
    # (If no findings exist yet, this will be None.)
    finding_points_by_submission = (
        GapFinding.objects.filter(submission__agent=agent_profile)
        .values("submission_id")
        .annotate(total_points=Sum("points"))
        .values_list("total_points", flat=True)
    )
    avg_coverage_score = None
    scores = [max(0, 100 - (p or 0)) for p in finding_points_by_submission]
    if scores:
        avg_coverage_score = sum(scores) / len(scores)

    context = {
        "agent_profile": agent_profile,
        "total_submissions": total_submissions,
        "recent_submissions": recent_submissions,
        "referral_count": referral_count,
        "avg_coverage_score": avg_coverage_score,
        "recent_links": recent_links,
    }
    return render(request, "dashboard/index.html", context)
