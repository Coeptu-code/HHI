from __future__ import annotations

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.agents.models import AgentProfile
from apps.customers.models import AgentNote, CoverageItem, CustomerActivity, CustomerRecord, PreCallSummary
from apps.intake.models import HouseholdMember, IntakeAnswer, IntakeSubmission
from apps.intake.services import analyze_intake_session
from apps.questionnaires.models import QuestionnaireLink


class CustomerIntelligenceEndpointTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="agent1", password="pass123456")
        self.agent = AgentProfile.objects.create(user=self.user, agency_name="Hutchins")
        self.link = QuestionnaireLink.objects.create(agent=self.agent)

        self.customer = CustomerRecord.objects.create(
            agent=self.agent,
            first_name="Garrett",
            last_name="Mills",
            email="garrett@example.com",
            phone="5551112222",
            state="TX",
            status="active",
        )
        self.customer_no_data = CustomerRecord.objects.create(
            agent=self.agent,
            first_name="No",
            last_name="Data",
            email="nodata@example.com",
            state="OK",
            status="prospect",
        )

        self.submission = IntakeSubmission.objects.create(
            questionnaire_link=self.link,
            agent=self.agent,
            customer=self.customer,
            status="submitted",
            submitted_at=timezone.now(),
            public_token="submission-analysis-token",
            source="test",
        )
        HouseholdMember.objects.create(
            submission=self.submission,
            customer=self.customer,
            role="primary",
            name="Garrett Mills",
            first_name="Garrett",
            last_name="Mills",
            date_of_birth="1988-01-01",
            dob="1988-01-01",
            needs_coverage=True,
            needs_health_coverage=True,
            takes_prescriptions=True,
            has_prescriptions=True,
        )
        HouseholdMember.objects.create(
            submission=self.submission,
            customer=self.customer,
            role="spouse",
            name="Jules Mills",
            first_name="Jules",
            last_name="Mills",
            date_of_birth="1989-02-02",
            dob="1989-02-02",
            needs_coverage=False,
            needs_health_coverage=False,
        )
        HouseholdMember.objects.create(
            submission=self.submission,
            customer=self.customer,
            role="dependent",
            name="Kid Mills",
            first_name="Kid",
            last_name="Mills",
            date_of_birth="2015-03-03",
            dob="2015-03-03",
            needs_coverage=True,
            needs_health_coverage=True,
        )

        answer_map = {
            "current_health_coverage": "none",
            "want_marketplace_help": "yes",
            "has_life_insurance": "no",
            "spouse_coverage": "none",
            "has_vision_coverage": "none",
            "has_dental_coverage": "none",
            "has_umbrella": "no",
            "assets_over_250k": "yes",
            "has_auto_insurance": "yes",
            "auto_liability_limit": "low",
            "owns_home": "yes",
            "has_home_insurance": "no",
            "owns_rental_property": "yes",
            "main_concern": "Need help with health insurance",
            "consent_referral_sharing": "yes",
        }
        for key, value in answer_map.items():
            IntakeAnswer.objects.create(
                submission=self.submission,
                customer=self.customer,
                question_key=key,
                question_text=key,
                answer_value=value,
            )

        CoverageItem.objects.create(
            customer=self.customer,
            coverage_type="medical",
            status="gap",
            gap_label="No current health coverage",
        )
        CoverageItem.objects.create(
            customer=self.customer,
            coverage_type="auto_home",
            status="referral_opportunity",
            gap_label="Bundling opportunity",
        )

        AgentNote.objects.create(
            customer=self.customer,
            intake_session=self.submission,
            note_type="do_not_bring_up",
            note="Avoid discussing pre-existing condition details early in call.",
        )

        analyze_intake_session(self.submission.id)
        CustomerActivity.objects.create(
            customer=self.customer,
            intake_session=self.submission,
            activity_type="manual_review",
            title="Manual review completed",
            description="Agent reviewed findings.",
            actor_type="agent",
            actor_name="Hutchins",
        )

        self.client.force_login(self.user)

    def test_customers_list_returns_enriched_rows(self) -> None:
        response = self.client.get(
            f"{reverse('customer_list')}?format=json&search=garrett&has_health_gaps=true&min_gap_score=10"
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("results", payload)
        self.assertEqual(payload["count"], 1)

        row = payload["results"][0]
        self.assertEqual(row["id"], self.customer.id)
        self.assertIn("gap_score", row)
        self.assertIn("health_gap_count", row)
        self.assertIn("referral_gap_count", row)
        self.assertIn("top_finding_title", row)

    def test_customer_detail_includes_household_coverage_score_talking_points_activity_and_findings(self) -> None:
        response = self.client.get(f"{reverse('customer_detail', args=[self.customer.id])}?format=json")
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("customer", payload)
        self.assertIn("household", payload)
        self.assertIn("coverage_items", payload)
        self.assertIn("score", payload)
        self.assertIn("top_talking_points", payload)
        self.assertIn("recent_activity", payload)
        self.assertIn("findings", payload)
        self.assertGreaterEqual(len(payload["household"]), 1)
        self.assertGreaterEqual(payload["score"]["finding_count"], 1)

    def test_pre_call_summary_returns_avery_read_and_ordered_talking_points(self) -> None:
        response = self.client.get(reverse("customer_pre_call_summary", args=[self.customer.id]))
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("summary", payload)
        self.assertIn("avery_read", payload["summary"])
        self.assertIn("talking_points", payload)
        self.assertGreaterEqual(len(payload["talking_points"]), 1)
        if len(payload["talking_points"]) > 1:
            self.assertGreaterEqual(
                payload["talking_points"][0]["priority"],
                payload["talking_points"][1]["priority"],
            )

    def test_submission_analysis_returns_talking_points_findings_household_and_score(self) -> None:
        response = self.client.get(reverse("submission_analysis", args=[self.submission.id]))
        self.assertEqual(response.status_code, 200)
        payload = response.json()

        self.assertIn("key_talking_points", payload)
        self.assertIn("findings", payload)
        self.assertIn("household", payload)
        self.assertIn("score", payload)
        self.assertGreaterEqual(payload["score"]["finding_count"], 1)

    def test_pre_call_summary_regeneration_is_idempotent(self) -> None:
        url = reverse("customer_pre_call_summary_regenerate", args=[self.customer.id])
        first = self.client.post(url)
        second = self.client.post(url)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(
            PreCallSummary.objects.filter(customer=self.customer, intake_session=self.submission).count(),
            1,
        )

    def test_missing_optional_data_does_not_crash_endpoints(self) -> None:
        response = self.client.get(f"{reverse('customer_detail', args=[self.customer_no_data.id])}?format=json")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["customer"]["id"], self.customer_no_data.id)
        self.assertEqual(payload["household"], [])
        self.assertEqual(payload["findings"], [])

    def test_customer_activity_endpoint_returns_newest_first(self) -> None:
        CustomerActivity.objects.create(
            customer=self.customer,
            intake_session=self.submission,
            activity_type="email_sent",
            title="Email sent",
            actor_type="agent",
            actor_name="Hutchins",
        )
        response = self.client.get(reverse("customer_activity", args=[self.customer.id]))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("items", payload)
        self.assertGreaterEqual(len(payload["items"]), 2)
        self.assertGreaterEqual(payload["items"][0]["created_at"], payload["items"][1]["created_at"])

    def test_customer_assignment_endpoint_updates_assignment_and_records_activity(self) -> None:
        user_model = get_user_model()
        other_user = user_model.objects.create_user(username="agent3", password="pass123456")
        other_agent = AgentProfile.objects.create(user=other_user, agency_name="Secondary")
        response = self.client.patch(
            reverse("customer_assignment_update", args=[self.customer.id]),
            data=f'{{"assigned_agent_id": {other_agent.id}}}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        self.customer.refresh_from_db()
        self.assertEqual(self.customer.agent_id, other_agent.id)
        self.assertTrue(
            CustomerActivity.objects.filter(
                customer=self.customer,
                activity_type="agent_assignment_updated",
            ).exists()
        )

    def test_do_not_bring_up_note_appears_in_pre_call_summary(self) -> None:
        response = self.client.get(reverse("customer_pre_call_summary", args=[self.customer.id]))
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertIn("do_not_bring_up", payload)
        self.assertTrue(
            any("pre-existing condition" in note for note in payload["do_not_bring_up"])
        )
