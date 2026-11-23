"""Owner-only, audited release back into the unassigned ticket queue."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, IssueChange, Priority


class ReleaseTicketTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.owner = get_user_model().objects.create_user(username='release-owner')
        cls.other = get_user_model().objects.create_user(username='release-other')
        cls.viewer = get_user_model().objects.create_user(username='release-viewer')
        grant = Permission.objects.filter(
            content_type__app_label='issues',
            codename__in=('view_issue', 'change_issue'),
        )
        cls.owner.user_permissions.add(*grant)
        cls.other.user_permissions.add(*grant)
        cls.viewer.user_permissions.add(Permission.objects.get(
            content_type__app_label='issues', codename='view_issue',
        ))
        priority = Priority.objects.create(name='Normal')
        cls.ticket = Issue.objects.create(
            requestor_name='Requester', summary='VPN issue',
            description='VPN support', priority=priority,
            pub_date=timezone.now(), issue_open=True, assigned=cls.owner,
        )

    def endpoint(self):
        return reverse('issues:issue_release', args=[self.ticket.pk])

    def test_owner_release_creates_one_audit_event_and_unassigns(self):
        self.client.force_login(self.owner)
        response = self.client.post(self.endpoint())
        self.assertRedirects(response, reverse('issues:issue', args=[self.ticket.pk]))
        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.assigned_id)
        change = IssueChange.objects.get(issue=self.ticket)
        self.assertEqual(change.actor, self.owner)
        self.assertEqual(change.before['assigned']['id'], self.owner.pk)
        self.assertEqual(change.after['assigned']['name'], 'Unassigned')
        self.assertEqual(change.before['status'], change.after['status'])

    def test_different_agent_cannot_release_someone_elses_ticket(self):
        self.client.force_login(self.other)
        response = self.client.post(self.endpoint())
        self.assertEqual(response.status_code, 409)
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned, self.owner)
        self.assertFalse(IssueChange.objects.filter(issue=self.ticket).exists())

    def test_repeated_release_is_noop_conflict(self):
        self.client.force_login(self.owner)
        self.client.post(self.endpoint())
        self.assertEqual(self.client.post(self.endpoint()).status_code, 409)
        self.assertEqual(IssueChange.objects.filter(issue=self.ticket).count(), 1)

    def test_closed_ticket_cannot_be_released(self):
        self.ticket.issue_open = False
        self.ticket.save(update_fields=['issue_open'])
        self.client.force_login(self.owner)
        self.assertEqual(self.client.post(self.endpoint()).status_code, 409)
        self.assertEqual(Issue.objects.get(pk=self.ticket.pk).assigned_id, self.owner.pk)

    def test_viewer_anonymous_get_and_missing_id_cannot_release(self):
        self.client.force_login(self.viewer)
        self.assertEqual(self.client.post(self.endpoint()).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.post(self.endpoint()).status_code, 302)
        self.client.force_login(self.owner)
        self.assertEqual(self.client.get(self.endpoint()).status_code, 405)
        self.assertEqual(self.client.post(reverse(
            'issues:issue_release', args=[99999999],
        )).status_code, 404)
        self.assertEqual(Issue.objects.get(pk=self.ticket.pk).assigned_id, self.owner.pk)

    def test_release_button_visible_only_to_owner_for_open_tickets(self):
        self.client.force_login(self.owner)
        self.assertContains(
            self.client.get(reverse('issues:index')),
            'aria-label="Release ticket',
        )
        self.client.force_login(self.other)
        self.assertNotContains(
            self.client.get(reverse('issues:index')),
            'aria-label="Release ticket',
        )
        self.client.force_login(self.owner)
        self.client.post(self.endpoint())
        self.assertNotContains(
            self.client.get(reverse('issues:index')),
            'aria-label="Release ticket',
        )

    def test_csrf_is_enforced(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.owner)
        self.assertEqual(client.post(self.endpoint()).status_code, 403)
        self.assertEqual(Issue.objects.get(pk=self.ticket.pk).assigned_id, self.owner.pk)
