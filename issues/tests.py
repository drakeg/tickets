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

    def test_issue_create_requires_authentication(self):
        response = self.client.get(reverse("issues:issue_new"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_my_issues_requires_authentication(self):
        response = self.client.get(reverse("issues:my_issues"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

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

        created = Issue.objects.get(summary="VPN access")
        self.assertEqual(created.requestor_name, self.user.username)
        self.assertEqual(created.assigned, self.user)

        self.assertRedirects(
            response, reverse("issues:issue", args=[created.pk])
        )
        self.client.get(response["Location"])
        self.assertEqual(Issue.objects.filter(summary="VPN access").count(), 1)

    def test_invalid_submission_keeps_errors_and_does_not_create_ticket(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("issues:issue_new"),
            {"summary": "", "description": "Keep this text", "priority": self.priority.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "summary", "This field is required.")
        self.assertContains(response, "Keep this text")
        self.assertEqual(Issue.objects.count(), 1)

    def test_detail_displays_ticket_fields(self):
        response = self.client.get(reverse("issues:issue", args=[self.issue.pk]))
        for value in ("Printer unavailable", "Office printer is offline", "Normal", "Open", "issue-user"):
            self.assertContains(response, value)
        self.assertContains(response, reverse("issues:index"))

    def test_detail_displays_closed_unassigned_ticket_and_escapes_description(self):
        self.issue.issue_open = False
        self.issue.assigned = None
        self.issue.description = '<script>alert("unsafe")</script>\nSecond line'
        self.issue.save()
        response = self.client.get(reverse("issues:issue", args=[self.issue.pk]))
        self.assertContains(response, "Closed")
        self.assertContains(response, "Unassigned")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("unsafe")</script>')
        self.assertContains(response, "<br>Second line")

    def test_missing_ticket_returns_404(self):
        response = self.client.get(reverse("issues:issue", args=[self.issue.pk + 1]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_submission_cannot_create_ticket(self):
        response = self.client.post(reverse("issues:issue_new"), {
            "summary": "Unauthorized", "description": "Blocked", "priority": self.priority.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
        self.assertEqual(Issue.objects.count(), 1)
