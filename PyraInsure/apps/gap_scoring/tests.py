from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from apps.agents.models import AgentProfile
from apps.customers.models import CustomerRecord
from apps.gap_scoring.models import RuleConfig, ScoringWeight, TalkingPoint, TalkingPointTemplate
from apps.intake.models import HouseholdMember, IntakeAnswer, IntakeSubmission
from apps.intake.services import analyze_intake_session
from apps.questionnaires.models import QuestionnaireLink


class RuleAndTemplateConfigTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="agent1", password="testpass123")
        self.agent = AgentProfile.objects.create(user=self.user)
        self.customer = CustomerRecord.objects.create(agent=self.agent, first_name="Casey", last_name="River")
        self.link = QuestionnaireLink.objects.create(agent=self.agent)

    def _submission(self) -> IntakeSubmission:
        submission = IntakeSubmission.objects.create(
            questionnaire_link=self.link,
            agent=self.agent,
            customer=self.customer,
            status="submitted",
            submitted_at=timezone.now(),
            public_token=f"s-{timezone.now().timestamp()}",
        )
        HouseholdMember.objects.create(
            submission=submission,
            customer=self.customer,
            role="primary",
            name="Casey River",
            first_name="Casey",
            last_name="River",
            date_of_birth="1990-01-01",
            needs_coverage=True,
            needs_health_coverage=True,
        )
        IntakeAnswer.objects.create(
            submission=submission,
            customer=self.customer,
            question_key="current_health_coverage",
            question_text="coverage",
            answer_value="none",
        )
        return submission

    def test_rule_config_disables_rule(self) -> None:
        RuleConfig.objects.filter(rule_key="health_gap").update(enabled=False)
        submission = self._submission()

        analyze_intake_session(submission.id)

        self.assertFalse(submission.gap_findings.filter(finding_type="health_gap").exists())

    def test_rule_config_and_weight_changes_points_used_by_scoring(self) -> None:
        RuleConfig.objects.filter(rule_key="health_gap").update(enabled=True, points=45)
        ScoringWeight.objects.filter(weight_key="health_gap").update(value=42, enabled=True)
        submission = self._submission()

        analyze_intake_session(submission.id)

        finding = submission.gap_findings.get(finding_type="health_gap")
        self.assertEqual(finding.points, 42)

    def test_talking_point_template_changes_generated_script(self) -> None:
        TalkingPointTemplate.objects.filter(template_key="health_gap").update(
            suggested_script="Custom script for health gap."
        )
        submission = self._submission()

        analyze_intake_session(submission.id)

        talking_point = TalkingPoint.objects.filter(intake_session=submission, title__icontains="Health").first()
        self.assertIsNotNone(talking_point)
        self.assertEqual(talking_point.suggested_script, "Custom script for health gap.")
