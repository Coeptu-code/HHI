from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from apps.agents.models import AgentProfile
from apps.questionnaires.forms import QuestionnaireLinkCreateForm
from apps.questionnaires.models import QuestionnaireLink


@login_required
def create_questionnaire_link(request):
    agent_profile, _ = AgentProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        form = QuestionnaireLinkCreateForm(request.POST)
        if form.is_valid():
            link: QuestionnaireLink = form.save(commit=False)
            link.agent = agent_profile
            link.save()
            return redirect("questionnaire_link_created", link_id=link.id)
    else:
        form = QuestionnaireLinkCreateForm(
            initial={
                "include_health": True,
                "include_life": True,
                "include_auto": True,
                "include_home": True,
                "include_umbrella": True,
            }
        )

    return render(request, "questionnaires/create_link.html", {"form": form, "active_nav": "links"})


@login_required
def link_created(request, link_id: int):
    link = get_object_or_404(QuestionnaireLink, id=link_id, agent__user=request.user)
    intake_url = request.build_absolute_uri(reverse("intake_entry", args=[link.token]))
    return render(request, "questionnaires/link_created.html", {"link": link, "intake_url": intake_url, "active_nav": "links"})
