"""Ticket-detail ownership controls reuse the protected claim/release endpoints."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, IssueChange, Priority


class DetailOwnershipControlsTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.agent = get_user_model().objects.create_user(username="detail-agent")
        cls.other = get_user_model().objects.create_user(username="detail-other")
        cls.reader = get_user_model().objects.create_user(username="detail-reader")
        grants = Permission.objects.filter(
            content_type__app_label="issues",
            codename__in=("view_issue", "change_issue"),
        )
        cls.agent.user_permissions.add(*grants)
        cls.other.user_permissions.add(*grants)
        cls.reader.user_permissions.add(Permission.objects.get(
            content_type__app_label="issues", codename="view_issue",
        ))
        cls.ticket = Issue.objects.create(
            requestor_name="Tester", summary="Account access",
            description="Access denied", priority=Priority.objects.create(name="Normal"),
            assigned=None, pub_date=timezone.now(),
        )

    def detail_url(self):
        return reverse("issues:issue", args=[self.ticket.pk])

    def test_open_unassigned_ticket_shows_claim_for_editor(self):
        self.client.force_login(self.agent)
        response = self.client.get(self.detail_url())
        self.assertContains(response, "Claim this ticket")
        self.assertContains(response, reverse("issues:issue_claim", args=[self.ticket.pk]))
        self.assertContains(response, "csrfmiddlewaretoken")
        self.assertNotContains(response, "Release my ticket")

    def test_claimed_ticket_shows_release_only_to_owner(self):
        self.client.force_login(self.agent)
        self.client.post(reverse("issues:issue_claim", args=[self.ticket.pk]))
        response = self.client.get(self.detail_url())
        self.assertContains(response, "Release my ticket")
        self.assertNotContains(response, "Claim this ticket")
        self.client.force_login(self.other)
        response = self.client.get(self.detail_url())
        self.assertNotContains(response, "Release my ticket")
        self.assertNotContains(response, "Claim this ticket")

    def test_read_only_user_sees_no_ownership_actions(self):
        self.client.force_login(self.reader)
        response = self.client.get(self.detail_url())
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Claim this ticket")
        self.assertNotContains(response, "Release my ticket")

    def test_closed_tickets_never_show_claim_or_release_controls(self):
        self.ticket.issue_open = False
        self.ticket.save(update_fields=["issue_open"])
        self.client.force_login(self.agent)
        response = self.client.get(self.detail_url())
        self.assertNotContains(response, "Claim this ticket")
        self.assertNotContains(response, "Release my ticket")

    def test_detail_buttons_call_real_audited_routes(self):
        self.client.force_login(self.agent)
        self.client.post(reverse("issues:issue_claim", args=[self.ticket.pk]))
        self.client.post(reverse("issues:issue_release", args=[self.ticket.pk]))
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.assigned_id)
        changes = IssueChange.objects.filter(issue=self.ticket)
        self.assertEqual(changes.count(), 2)
        self.assertEqual(changes.first().after["assigned"]["name"], "Unassigned")
        self.assertEqual(changes.last().after["assigned"]["id"], self.agent.pk)
