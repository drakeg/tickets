from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Issue, Priority


class IssueWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="issue-user",
            password="test-password",
        )
        self.priority = Priority.objects.create(name="Normal")
        self.issue = Issue.objects.create(
            requestor_name="issue-user",
            summary="Printer unavailable",
            description="Office printer is offline",
            priority=self.priority,
            pub_date=timezone.now(),
            assigned=self.user,
        )

    def test_issue_detail_returns_requested_issue(self):
        response = self.client.get(reverse("issues:issue", args=[self.issue.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["issue"], self.issue)

    def test_issue_search_matches_summary_or_description(self):
        response = self.client.get(reverse("issues:search"), {"q": "printer"})

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["issue_list"],
            [self.issue],
            transform=lambda issue: issue,
        )

    def test_empty_issue_search_returns_empty_result(self):
        response = self.client.get(reverse("issues:search"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["issue_list"]), [])

    def test_issue_form_creates_issue(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issues:issue_new"),
            {
                "summary": "VPN access",
                "description": "Unable to connect to VPN",
                "priority": self.priority.pk,
                "assigned": self.user.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        created = Issue.objects.get(summary="VPN access")
        self.assertEqual(created.requestor_name, self.user.username)
        self.assertEqual(created.assigned, self.user)
