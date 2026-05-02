from __future__ import annotations

from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.agents.models import AgentProfile
from apps.customers.models import CustomerActivity, CustomerRecord
from apps.gap_scoring.models import GapFinding, TalkingPoint
from apps.intake.models import HouseholdMember, IntakeAnswer, IntakeSubmission
from apps.intake.conversation import build_turns
from apps.intake.services.address_lookup import StubAddressProvider, normalize_address_input
from apps.intake.services.intake_normalization import (
    detect_possible_full_name,
    normalize_date,
    normalize_email,
    normalize_income,
    normalize_liability_limit,
    normalize_name,
    normalize_phone,
    normalize_state,
    normalize_zip,
    split_full_name,
)
from apps.intake.services import analyze_intake_session
from apps.questionnaires.models import QuestionnaireLink


class IntakeAnalysisServiceTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="agent1", password="testpass123")
        self.agent = AgentProfile.objects.create(user=self.user, agency_name="Hutchins")
        self.link = QuestionnaireLink.objects.create(agent=self.agent)
        self.customer = CustomerRecord.objects.create(
            agent=self.agent,
            first_name="Test",
            last_name="Customer",
            email="test@example.com",
            phone="5551234567",
            state="TX",
        )

    def _create_submission(
        self,
        *,
        answers: dict[str, object] | None = None,
        members: list[dict[str, object]] | None = None,
    ) -> IntakeSubmission:
        submission = IntakeSubmission.objects.create(
            questionnaire_link=self.link,
            agent=self.agent,
            customer=self.customer,
            status="submitted",
            submitted_at=timezone.now(),
            public_token=f"session-{timezone.now().timestamp()}",
            source="test",
        )

        member_rows = members or [
            {"role": "primary", "first_name": "Test", "last_name": "Customer", "needs_coverage": True, "takes_prescriptions": False}
        ]
        for row in member_rows:
            first_name = str(row.get("first_name", "Member"))
            last_name = str(row.get("last_name", ""))
            full_name = f"{first_name} {last_name}".strip()
            needs_coverage = bool(row.get("needs_coverage", False))
            takes_prescriptions = bool(row.get("takes_prescriptions", False))
            HouseholdMember.objects.create(
                submission=submission,
                customer=self.customer,
                role=str(row.get("role", "dependent")),
                name=full_name,
                first_name=first_name,
                last_name=last_name,
                date_of_birth="1990-01-01",
                dob="1990-01-01",
                needs_coverage=needs_coverage,
                needs_health_coverage=needs_coverage,
                takes_prescriptions=takes_prescriptions,
                has_prescriptions=takes_prescriptions,
            )

        for key, value in (answers or {}).items():
            if isinstance(value, bool):
                answer_value = "yes" if value else "no"
            else:
                answer_value = str(value)
            IntakeAnswer.objects.create(
                submission=submission,
                customer=self.customer,
                question_key=key,
                question_text=key,
                answer_value=answer_value,
            )

        return submission

    def test_health_gap_creates_critical_30_point_finding(self) -> None:
        submission = self._create_submission(answers={"current_health_coverage": "none"})

        analyze_intake_session(submission.id)

        finding = GapFinding.objects.get(submission=submission, finding_type="health_gap")
        self.assertEqual(finding.severity, "critical")
        self.assertEqual(finding.points, 30)

    def test_assets_over_250k_without_umbrella_creates_umbrella_finding(self) -> None:
        submission = self._create_submission(
            answers={
                "current_health_coverage": "employer",
                "assets_over_250k": "yes",
                "has_umbrella": "no",
            },
            members=[{"role": "primary", "first_name": "Test", "last_name": "Customer", "needs_coverage": False}],
        )

        analyze_intake_session(submission.id)

        self.assertTrue(GapFinding.objects.filter(submission=submission, finding_type="umbrella_gap").exists())

    def test_spouse_or_dependents_without_life_coverage_creates_life_finding(self) -> None:
        submission = self._create_submission(
            answers={
                "current_health_coverage": "employer",
                "has_life_insurance": "no",
            },
            members=[
                {"role": "primary", "first_name": "Test", "last_name": "Customer", "needs_coverage": False},
                {"role": "spouse", "first_name": "Pat", "last_name": "Customer", "needs_coverage": False},
            ],
        )

        analyze_intake_session(submission.id)

        self.assertTrue(GapFinding.objects.filter(submission=submission, finding_type="life_gap").exists())

    def test_repeated_analysis_is_idempotent_for_findings_and_talking_points(self) -> None:
        submission = self._create_submission(
            answers={
                "current_health_coverage": "none",
                "want_marketplace_help": "yes",
                "has_umbrella": "no",
                "assets_over_250k": "yes",
            }
        )

        first_result = analyze_intake_session(submission.id)
        second_result = analyze_intake_session(submission.id)

        self.assertEqual(len(first_result.findings), len(second_result.findings))
        self.assertEqual(len(first_result.talking_points), len(second_result.talking_points))
        self.assertEqual(
            GapFinding.objects.filter(submission=submission).count(),
            len(second_result.findings),
        )
        self.assertEqual(
            TalkingPoint.objects.filter(intake_session=submission).count(),
            len(second_result.talking_points),
        )
        self.assertEqual(
            CustomerActivity.objects.filter(
                customer=self.customer,
                intake_session=submission,
                activity_type="intake_analyzed",
            ).count(),
            1,
        )

    def test_score_is_capped_at_100(self) -> None:
        submission = self._create_submission(
            answers={
                "current_health_coverage": "none",
                "want_marketplace_help": "yes",
                "has_vision_coverage": "none",
                "has_dental_coverage": "none",
                "has_life_insurance": "no",
                "spouse_coverage": "none",
                "owns_home": "yes",
                "has_home_insurance": "no",
                "owns_rental_property": "yes",
                "assets_over_250k": "yes",
                "has_umbrella": "no",
                "has_auto_insurance": "yes",
                "auto_liability_limit": "low",
            },
            members=[
                {"role": "primary", "first_name": "Test", "last_name": "Customer", "needs_coverage": True, "takes_prescriptions": True},
                {"role": "spouse", "first_name": "Pat", "last_name": "Customer", "needs_coverage": False},
                {"role": "dependent", "first_name": "Kid", "last_name": "Customer", "needs_coverage": True},
            ],
        )

        result = analyze_intake_session(submission.id)

        self.assertGreater(result.raw_gap_score, 100)
        self.assertEqual(result.capped_gap_score, 100)
        self.customer.refresh_from_db()
        self.assertEqual(float(self.customer.avg_gap_score), 100.0)

    def test_talking_points_follow_priority_order(self) -> None:
        submission = self._create_submission(
            answers={
                "current_health_coverage": "none",
                "want_marketplace_help": "yes",
                "has_life_insurance": "no",
            },
            members=[
                {"role": "primary", "first_name": "Test", "last_name": "Customer", "needs_coverage": True},
                {"role": "spouse", "first_name": "Pat", "last_name": "Customer", "needs_coverage": False},
            ],
        )

        analyze_intake_session(submission.id)

        talking_points = list(TalkingPoint.objects.filter(intake_session=submission).order_by("-priority", "id"))
        self.assertGreater(len(talking_points), 1)
        self.assertGreaterEqual(talking_points[0].priority, talking_points[1].priority)
        titles = [point.title for point in talking_points]
        self.assertLess(
            titles.index("Health coverage for household members"),
            titles.index("Marketplace / ACA follow-up"),
        )


class IntakeManagementFlowTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="agent2", password="testpass123")
        self.agent = AgentProfile.objects.create(user=self.user, agency_name="Hutchins")
        self.link = QuestionnaireLink.objects.create(agent=self.agent, status="created")
        self.customer = CustomerRecord.objects.create(
            agent=self.agent,
            first_name="Taylor",
            last_name="Lane",
            email="taylor@example.com",
            state="TX",
        )
        self.link.customer = self.customer
        self.link.save(update_fields=["customer"])
        self.client.force_login(self.user)

    def _create_submission_with_answers(self) -> IntakeSubmission:
        submission = IntakeSubmission.objects.create(
            questionnaire_link=self.link,
            agent=self.agent,
            customer=self.customer,
            status="submitted",
            submitted_at=timezone.now(),
            public_token=f"submission-{timezone.now().timestamp()}",
            source="test",
        )
        HouseholdMember.objects.create(
            submission=submission,
            customer=self.customer,
            role="primary",
            name="Taylor Lane",
            first_name="Taylor",
            last_name="Lane",
            date_of_birth="1990-01-01",
            needs_coverage=True,
            needs_health_coverage=True,
        )
        IntakeAnswer.objects.create(
            submission=submission,
            customer=self.customer,
            question_key="current_health_coverage",
            question_text="Coverage",
            answer_value="none",
        )
        IntakeAnswer.objects.create(
            submission=submission,
            customer=self.customer,
            question_key="has_life_insurance",
            question_text="Life",
            answer_value="no",
        )
        return submission

    def test_manual_finding_survives_reanalysis(self) -> None:
        submission = self._create_submission_with_answers()
        analyze_intake_session(submission.id)
        manual = GapFinding.objects.create(
            submission=submission,
            customer=self.customer,
            finding_type="manual_override",
            category="health",
            severity="low",
            points=1,
            title="Manual keep",
            assigned_to="hutchins",
            is_generated=False,
            status="open",
        )

        analyze_intake_session(submission.id)

        self.assertTrue(GapFinding.objects.filter(id=manual.id).exists())
        self.assertFalse(GapFinding.objects.get(id=manual.id).is_generated)

    def test_submission_review_updates_status_and_records_activity(self) -> None:
        submission = self._create_submission_with_answers()
        response = self.client.patch(
            reverse("admin_submission_review", args=[submission.id]),
            data='{"review_status":"reviewed","review_notes":"Looks good"}',
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        submission.refresh_from_db()
        self.assertEqual(submission.review_status, "reviewed")
        self.assertIsNotNone(submission.reviewed_at)
        self.assertTrue(
            CustomerActivity.objects.filter(
                customer=self.customer,
                intake_session=submission,
                activity_type="manual_review_completed",
            ).exists()
        )

    def test_intake_link_open_increments_open_count_and_records_started_once(self) -> None:
        self.client.get(reverse("intake_entry", args=[self.link.token]))
        self.client.get(reverse("intake_entry", args=[self.link.token]))
        self.link.refresh_from_db()

        self.assertEqual(self.link.open_count, 2)
        self.assertEqual(self.link.status, "started")
        self.assertEqual(
            CustomerActivity.objects.filter(
                customer=self.customer,
                activity_type="intake_started",
            ).count(),
            1,
        )

    def test_intake_submit_records_submitted_and_analyzed_activity(self) -> None:
        token = self.link.token
        session = self.client.session
        session[f"intake_wizard_{token}"] = {
            "basic_info": {
                "first_name": "Taylor",
                "last_name": "Lane",
                "email": "taylor@example.com",
                "phone": "5551234567",
                "state": "TX",
                "preferred_contact_method": "email",
                "primary_date_of_birth": "1990-01-01",
            },
            "household_members": [
                {
                    "temp_id": "primary",
                    "role": "primary",
                    "first_name": "Taylor",
                    "last_name": "Lane",
                    "date_of_birth": "1990-01-01",
                    "needs_coverage": True,
                    "other_coverage_access": False,
                    "legal_parent_guardian_under_19": False,
                    "claimed_tax_dependent": False,
                    "pregnant": False,
                    "tobacco_user": False,
                    "takes_prescriptions": False,
                }
            ],
            "answers": {"current_health_coverage": "none", "want_marketplace_help": "yes"},
            "consents": {},
            "prescriptions": {},
        }
        session.save()

        response = self.client.post(
            reverse("intake_submit", args=[token]),
            data={
                "consent_terms": "on",
                "consent_privacy": "on",
                "consent_contact": "on",
                "consent_referral_sharing": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        submission = IntakeSubmission.objects.filter(questionnaire_link=self.link).order_by("-id").first()
        self.assertIsNotNone(submission)
        self.assertTrue(
            CustomerActivity.objects.filter(
                customer=self.customer,
                intake_session=submission,
                activity_type="intake_submitted",
            ).exists()
        )
        self.assertTrue(
            CustomerActivity.objects.filter(
                customer=self.customer,
                intake_session=submission,
                activity_type="intake_analyzed",
            ).exists()
        )


class IntakeNormalizationUtilityTests(TestCase):
    def test_normalize_date_formats(self) -> None:
        self.assertEqual(normalize_date("1/5/90").display, "01/05/1990")
        self.assertEqual(normalize_date("01/05/1990").display, "01/05/1990")
        self.assertEqual(normalize_date("January 5 1990").display, "01/05/1990")
        self.assertEqual(normalize_date("Jan 5, 1990").display, "01/05/1990")
        self.assertEqual(normalize_date("1990-01-05").display, "01/05/1990")
        self.assertEqual(normalize_date("01051990").display, "01/05/1990")
        self.assertEqual(normalize_date("2/3/04").display, "02/03/2004")

    def test_normalize_date_validation(self) -> None:
        self.assertFalse(normalize_date("13/40/2020").ok)
        self.assertFalse(normalize_date("01/01/3000").ok)
        self.assertFalse(normalize_date("01/01/1800").ok)

    def test_normalize_phone_formats(self) -> None:
        self.assertEqual(normalize_phone("5555551212").display, "(555) 555-1212")
        self.assertEqual(normalize_phone("555-555-1212").display, "(555) 555-1212")
        self.assertEqual(normalize_phone("(555)5551212").display, "(555) 555-1212")
        self.assertEqual(normalize_phone("+1 555 555 1212").display, "(555) 555-1212")
        self.assertEqual(normalize_phone("555.555.1212").display, "(555) 555-1212")
        self.assertFalse(normalize_phone("5551212").ok)

    def test_name_normalization_and_full_name_detection(self) -> None:
        self.assertEqual(normalize_name("  daniel  "), "Daniel")
        self.assertEqual(normalize_name("mary-jane"), "Mary-Jane")
        self.assertEqual(normalize_name("o'connor"), "O'Connor")
        self.assertTrue(detect_possible_full_name("Daniel Gordon"))
        self.assertTrue(detect_possible_full_name("Mary Beth"))
        self.assertFalse(detect_possible_full_name("Jean-Luc"))
        self.assertFalse(detect_possible_full_name("O'Connor"))
        self.assertEqual(split_full_name("John A Doe"), ("John", "A Doe"))

    def test_zip_state_email_income_and_liability_normalization(self) -> None:
        self.assertEqual(normalize_zip("02108-1234").normalized, "02108")
        self.assertEqual(normalize_state("texas").normalized, "TX")
        self.assertEqual(normalize_email("  USER@Example.COM ").normalized, "user@example.com")
        self.assertEqual(normalize_income("$65,000").normalized, "65000")
        self.assertEqual(normalize_liability_limit("state_minimum").normalized, "low")
        self.assertEqual(normalize_liability_limit("high").normalized, "high")

    def test_address_preprocess_expands_abbreviations(self) -> None:
        self.assertEqual(normalize_address_input("34 Dalton ln"), "34 Dalton Lane")


class IntakeMessengerNormalizationTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="agent3", password="testpass123")
        self.agent = AgentProfile.objects.create(user=self.user, agency_name="Hutchins")
        self.link = QuestionnaireLink.objects.create(agent=self.agent, status="created")
        self.api_url = reverse("intake_messenger_api", args=[self.link.token])

    def _chat_post(self, payload: dict[str, object]) -> dict:
        response = self.client.post(
            self.api_url,
            data=payload,
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        return response.json()

    def test_full_name_entry_triggers_clarification_and_can_skip_last_name(self) -> None:
        self._chat_post({"turn_id": "intro", "answer": "__auto__"})
        first_name_response = self._chat_post({"turn_id": "first_name", "answer": "Daniel Gordon"})
        self.assertTrue(first_name_response["ok"])
        self.assertEqual(first_name_response["next"]["id"], "first_name_confirm")

        confirm_response = self._chat_post({"turn_id": "first_name_confirm", "answer": "__full_name__"})
        self.assertTrue(confirm_response["ok"])
        self.assertEqual(confirm_response["next"]["id"], "dob")

        session_data = self.client.session[f"intake_wizard_{self.link.token}"]
        self.assertEqual(session_data["basic_info"]["first_name"], "Daniel")
        self.assertEqual(session_data["basic_info"]["last_name"], "Gordon")

    def test_phone_response_displays_normalized_value(self) -> None:
        self._chat_post({"turn_id": "intro", "answer": "__auto__"})
        response = self._chat_post({"turn_id": "phone", "answer": "+1 555 555 1212"})
        self.assertTrue(response["ok"])
        self.assertEqual(response["user_display"], "(555) 555-1212")

    def test_submit_persists_raw_and_normalized_values(self) -> None:
        token = self.link.token
        session = self.client.session
        session[f"intake_wizard_{token}"] = {
            "basic_info": {
                "first_name": "Taylor",
                "last_name": "Lane",
                "email": "taylor@example.com",
                "phone": "(555) 555-1212",
                "state": "TX",
                "preferred_contact_method": "email",
                "primary_date_of_birth": "1990-01-05",
            },
            "household_members": [
                {
                    "temp_id": "primary",
                    "role": "primary",
                    "first_name": "Taylor",
                    "last_name": "Lane",
                    "date_of_birth": "1990-01-05",
                    "needs_coverage": True,
                    "other_coverage_access": False,
                    "legal_parent_guardian_under_19": False,
                    "claimed_tax_dependent": False,
                    "pregnant": False,
                    "tobacco_user": False,
                    "takes_prescriptions": False,
                }
            ],
            "answers": {"current_health_coverage": "none"},
            "consents": {},
            "prescriptions": {},
            "_raw_answers": {
                "phone": "5555551212",
                "primary_date_of_birth": "1/5/90",
            },
            "_normalized_answers": {
                "phone": "(555) 555-1212",
                "primary_date_of_birth": "01/05/1990",
            },
        }
        session.save()

        response = self.client.post(
            reverse("intake_submit", args=[token]),
            data={
                "consent_terms": "on",
                "consent_privacy": "on",
                "consent_contact": "on",
                "consent_referral_sharing": "on",
            },
        )
        self.assertEqual(response.status_code, 302)
        submission = IntakeSubmission.objects.filter(questionnaire_link=self.link).order_by("-id").first()
        self.assertIsNotNone(submission)
        assert submission is not None

        phone_answer = IntakeAnswer.objects.get(submission=submission, question_key="phone")
        dob_answer = IntakeAnswer.objects.get(submission=submission, question_key="primary_date_of_birth")
        self.assertEqual(phone_answer.answer_value, "5555551212")
        self.assertEqual(phone_answer.normalized_value["normalized_value"], "(555) 555-1212")
        self.assertEqual(dob_answer.answer_value, "1/5/90")
        self.assertEqual(dob_answer.normalized_value["display_value"], "01/05/1990")

    def test_address_lookup_with_stub_provider_confirms_candidate(self) -> None:
        provider = StubAddressProvider()
        result = provider.normalize_address("34 Dalton ln", zip_code="01604", state="MA")
        self.assertIn(result["status"], {"confirmed", "needs_confirmation"})
        self.assertTrue(result["suggestions"])
        self.assertIn("Dalton", result["suggestions"][0]["street"])

    def test_address_multiple_matches_prompts_selection(self) -> None:
        class FakeProvider:
            def lookup_address(self, query, zip_code=None, state=None):
                return {
                    "status": "multiple_matches",
                    "suggestions": [
                        {"street": "11 Main St", "city": "Austin", "state": "TX", "zip_code": "78701", "formatted": "11 Main St, Austin, TX 78701", "confidence": 0.8, "source": "stub"},
                        {"street": "12 Main St", "city": "Austin", "state": "TX", "zip_code": "78701", "formatted": "12 Main St, Austin, TX 78701", "confidence": 0.7, "source": "stub"},
                    ],
                }

        self._chat_post({"turn_id": "intro", "answer": "__auto__"})
        self._chat_post({"turn_id": "street_address", "answer": "11 main st"})
        with patch("apps.intake.views.get_address_provider", return_value=FakeProvider()):
            response = self._chat_post({"turn_id": "zip_code", "answer": "78701"})
        self.assertTrue(response["ok"])
        self.assertEqual(response["next"]["id"], "address_confirm")

    def test_address_no_match_triggers_retry(self) -> None:
        class FakeProvider:
            def lookup_address(self, query, zip_code=None, state=None):
                return {"status": "no_match", "suggestions": []}

        self._chat_post({"turn_id": "intro", "answer": "__auto__"})
        self._chat_post({"turn_id": "street_address", "answer": "999 unknown"})
        with patch("apps.intake.views.get_address_provider", return_value=FakeProvider()):
            response = self._chat_post({"turn_id": "zip_code", "answer": "78701"})
        self.assertFalse(response["ok"])
        self.assertIn("couldn't verify", response["error"].lower())


class IntakeBranchingTests(TestCase):
    def test_vehicle_no_skips_auto_section(self) -> None:
        turns = build_turns(
            {"basic_info": {}, "answers": {"owns_or_drives_vehicle": False}, "household_members": []},
            ["auto"],
        )
        turn_ids = [turn.id for turn in turns]
        self.assertIn("auto_owns_vehicle", turn_ids)
        self.assertNotIn("auto_has_insurance", turn_ids)
        self.assertNotIn("auto_liability", turn_ids)

    def test_homeowner_no_skips_homeowners_coverage_question(self) -> None:
        turns = build_turns(
            {"basic_info": {}, "answers": {"owns_home": False}, "household_members": []},
            ["home"],
        )
        turn_ids = [turn.id for turn in turns]
        self.assertIn("home_owns", turn_ids)
        self.assertNotIn("home_has_insurance", turn_ids)

    def test_umbrella_skipped_when_no_exposure(self) -> None:
        turns = build_turns(
            {
                "basic_info": {},
                "answers": {
                    "assets_over_250k": False,
                    "owns_home": False,
                    "owns_rental_property": False,
                    "teen_driver_in_household": False,
                    "has_extra_liability_risk": False,
                    "auto_liability_limit": "high",
                },
                "household_members": [],
            },
            ["umbrella"],
        )
        turn_ids = [turn.id for turn in turns]
        self.assertNotIn("umbrella_has", turn_ids)
