from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from apps.agents.models import AgentProfile
from apps.customers.models import CustomerActivity, CustomerRecord
from apps.intake.conversation import build_turns
from apps.intake.questions import get_visible_steps
from apps.questionnaires.models import QuestionnaireLink


class QuestionnaireCreateFlowTests(TestCase):
    def setUp(self) -> None:
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="agent-create", password="testpass123")
        self.agent = AgentProfile.objects.create(user=self.user, agency_name="Hutchins")
        self.client.force_login(self.user)

    def _post_payload(self, **overrides: object) -> dict[str, object]:
        payload: dict[str, object] = {
            "client_name": "Garrett Telman",
            "phone": "5551234567",
            "include_health": "on",
            "include_life": "on",
            "include_auto": "on",
            "include_home": "on",
            "include_umbrella": "on",
            "module_order": json.dumps(["home", "health", "auto", "life", "umbrella"]),
        }
        payload.update(overrides)
        return payload

    def test_create_link_persists_customer_delivery_and_module_order(self) -> None:
        response = self.client.post(reverse("create_questionnaire_link"), data=self._post_payload())
        self.assertEqual(response.status_code, 302)

        link = QuestionnaireLink.objects.order_by("-id").first()
        self.assertIsNotNone(link)
        assert link is not None
        self.assertEqual(link.status, "created")
        self.assertIsNone(link.delivery_method)
        self.assertEqual(link.module_order, ["home", "health", "auto", "life", "umbrella"])
        self.assertIsNotNone(link.customer_id)
        self.assertEqual(link.customer.phone, "5551234567")

    def test_create_link_reuses_existing_customer_by_phone(self) -> None:
        existing_customer = CustomerRecord.objects.create(
            agent=self.agent,
            first_name="Garrett",
            last_name="Telman",
            phone="5559998888",
            state="TX",
        )

        response = self.client.post(
            reverse("create_questionnaire_link"),
            data=self._post_payload(phone="5559998888"),
        )
        self.assertEqual(response.status_code, 302)
        link = QuestionnaireLink.objects.order_by("-id").first()
        self.assertIsNotNone(link)
        assert link is not None
        self.assertEqual(link.customer_id, existing_customer.id)
        self.assertEqual(CustomerRecord.objects.filter(agent=self.agent, phone="5559998888").count(), 1)

    def test_selected_modules_respects_saved_order_with_fallback(self) -> None:
        link = QuestionnaireLink.objects.create(
            agent=self.agent,
            include_health=True,
            include_life=True,
            include_auto=False,
            include_home=True,
            include_umbrella=True,
            module_order=["umbrella", "home", "life"],
        )
        self.assertEqual(link.selected_modules(), ["umbrella", "home", "life", "health"])

    def test_visible_steps_follow_major_module_order_and_keep_fixed_prefix_suffix(self) -> None:
        steps = get_visible_steps(["home", "health", "umbrella"])
        self.assertEqual(steps[0:2], ["basic", "household"])
        self.assertEqual(steps[-1], "consent")
        self.assertLess(steps.index("home"), steps.index("health"))
        self.assertLess(steps.index("health"), steps.index("umbrella"))
        self.assertIn("household_coverage", steps)
        self.assertIn("prescription_check", steps)

    def test_messenger_turns_follow_major_module_order(self) -> None:
        link = QuestionnaireLink.objects.create(
            agent=self.agent,
            include_health=True,
            include_life=True,
            include_auto=True,
            include_home=True,
            include_umbrella=True,
            module_order=["home", "health", "umbrella", "life", "auto"],
        )
        turns = build_turns(
            data={"basic_info": {}, "answers": {}, "household_members": []},
            modules=link.selected_modules(),
        )
        turn_ids = [turn.id for turn in turns]
        self.assertLess(turn_ids.index("home_owns"), turn_ids.index("health_coverage"))
        self.assertLess(turn_ids.index("health_coverage"), turn_ids.index("umbrella_has"))
        self.assertLess(turn_ids.index("umbrella_has"), turn_ids.index("life_dependents"))
        self.assertLess(turn_ids.index("life_dependents"), turn_ids.index("auto_owns_vehicle"))

    def test_create_link_records_activity(self) -> None:
        self.client.post(reverse("create_questionnaire_link"), data=self._post_payload())
        link = QuestionnaireLink.objects.order_by("-id").first()
        self.assertIsNotNone(link)
        assert link is not None
        self.assertTrue(
            CustomerActivity.objects.filter(
                customer_id=link.customer_id,
                activity_type="intake_link_created",
            ).exists()
        )

    def test_create_link_allows_blank_name_and_phone(self) -> None:
        response = self.client.post(
            reverse("create_questionnaire_link"),
            data=self._post_payload(client_name="", phone=""),
        )
        self.assertEqual(response.status_code, 302)
        link = QuestionnaireLink.objects.order_by("-id").first()
        self.assertIsNotNone(link)
        assert link is not None
        self.assertIsNone(link.customer_id)
