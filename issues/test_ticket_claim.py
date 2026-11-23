"""Claim-to-self: permissioned, audited, and fail-closed."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, IssueChange, Priority


class ClaimTicketTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.agent = get_user_model().objects.create_user(username='claim-agent')
        cls.second = get_user_model().objects.create_user(username='claim-second')
        cls.viewer = get_user_model().objects.create_user(username='claim-viewer')
        cls.agent.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='issues',
            codename__in=('view_issue', 'change_issue'),
        ))
        cls.second.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='issues',
            codename__in=('view_issue', 'change_issue'),
        ))
        cls.viewer.user_permissions.add(Permission.objects.get(
            content_type__app_label='issues', codename='view_issue',
        ))
        priority = Priority.objects.create(name='Normal')
        cls.ticket = Issue.objects.create(
            requestor_name='Requester', summary='Network down',
            description='Service unavailable', priority=priority,
            pub_date=timezone.now(), issue_open=True, assigned=None,
        )

    def endpoint(self, ticket=None):
        return reverse('issues:issue_claim', args=[(ticket or self.ticket).pk])

    def test_claim_assigns_current_user_and_writes_one_change(self):
        self.client.force_login(self.agent)
        response = self.client.post(self.endpoint())
        self.assertRedirects(response, reverse('issues:issue', args=[self.ticket.pk]))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned, self.agent)
        history = IssueChange.objects.get(issue=self.ticket)
        self.assertEqual(history.actor, self.agent)
        self.assertEqual(history.before['assigned']['name'], 'Unassigned')
        self.assertEqual(history.after['assigned']['id'], self.agent.pk)
        self.assertEqual(history.before['status'], 'Open')
        self.assertEqual(history.after['status'], 'Open')

    def test_second_agent_receives_conflict_without_reassigning(self):
        self.client.force_login(self.agent)
        self.client.post(self.endpoint())
        self.client.force_login(self.second)
        response = self.client.post(self.endpoint())
        self.assertEqual(response.status_code, 409)
        self.assertContains(response, 'already assigned or closed', status_code=409)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned, self.agent)
        self.assertEqual(IssueChange.objects.filter(issue=self.ticket).count(), 1)

    def test_repeated_claim_is_idempotent_and_returns_conflict(self):
        self.client.force_login(self.agent)
        self.client.post(self.endpoint())
        response = self.client.post(self.endpoint())
        self.assertEqual(response.status_code, 409)
        self.assertEqual(IssueChange.objects.filter(issue=self.ticket).count(), 1)

    def test_cannot_claim_closed_unassigned_ticket(self):
        self.ticket.issue_open = False
        self.ticket.save(update_fields=['issue_open'])
        self.client.force_login(self.agent)
        response = self.client.post(self.endpoint())
        self.assertEqual(response.status_code, 409)
        self.assertIsNone(Issue.objects.get(pk=self.ticket.pk).assigned_id)
        self.assertFalse(IssueChange.objects.filter(issue=self.ticket).exists())

    def test_read_only_or_anonymous_users_cannot_claim(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.post(self.endpoint()).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post(self.endpoint()).status_code, 302)
        self.assertIsNone(Issue.objects.get(pk=self.ticket.pk).assigned_id)

    def test_get_and_missing_ticket_cannot_mutate(self):
        self.client.force_login(self.agent)
        self.assertEqual(self.client.get(self.endpoint()).status_code, 405)
        self.assertEqual(self.client.post(reverse(
            'issues:issue_claim', args=[99999999],
        )).status_code, 404)
        self.assertIsNone(Issue.objects.get(pk=self.ticket.pk).assigned_id)

    def test_queue_shows_claim_only_for_editor_and_open_unassigned(self):
        self.client.force_login(self.agent)
        response = self.client.get(reverse('issues:index'))
        self.assertContains(response, 'aria-label="Claim ticket')
        self.assertContains(response, 'csrfmiddlewaretoken')
        self.client.post(self.endpoint())
        response = self.client.get(reverse('issues:index'))
        self.assertNotContains(response, 'aria-label="Claim ticket')
        self.client.force_login(self.viewer)
        response = self.client.get(reverse('issues:index'))
        self.assertNotContains(response, 'aria-label="Claim ticket')

    def test_csrf_check_applies_to_claim(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.agent)
        self.assertEqual(client.post(self.endpoint()).status_code, 403)
        self.assertIsNone(Issue.objects.get(pk=self.ticket.pk).assigned_id)
