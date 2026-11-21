"""Audited, permissioned one-click ticket status actions."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, IssueChange, Priority


class QueueQuickStatusTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user(username='queue-status-editor')
        cls.reader = get_user_model().objects.create_user(username='queue-status-reader')
        cls.editor.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='issues',
            codename__in=('view_issue', 'change_issue'),
        ))
        cls.reader.user_permissions.add(Permission.objects.get(
            content_type__app_label='issues', codename='view_issue',
        ))
        cls.priority = Priority.objects.create(name='High')
        cls.ticket = Issue.objects.create(
            requestor_name='Example', summary='Printer outage',
            description='Printer is offline', priority=cls.priority,
            assigned=cls.editor, pub_date=timezone.now(),
        )

    def endpoint(self):
        return reverse('issues:issue_quick_status', args=[self.ticket.pk])

    def test_close_and_reopen_add_actor_attributed_history(self):
        self.client.force_login(self.editor)
        response = self.client.post(self.endpoint(), {'action': 'close'})
        self.assertRedirects(
            response, reverse('issues:issue', args=[self.ticket.pk]),
        )
        self.ticket.refresh_from_db()
        self.assertFalse(self.ticket.issue_open)
        event = IssueChange.objects.get(issue=self.ticket)
        self.assertEqual(event.actor, self.editor)
        self.assertEqual(event.before['status'], 'Open')
        self.assertEqual(event.after['status'], 'Closed')
        self.client.post(self.endpoint(), {'action': 'reopen'})
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.issue_open)
        self.assertEqual(IssueChange.objects.filter(issue=self.ticket).count(), 2)

    def test_duplicate_action_is_idempotent_and_does_not_rewrite_history(self):
        self.client.force_login(self.editor)
        self.client.post(self.endpoint(), {'action': 'close'})
        self.client.post(self.endpoint(), {'action': 'close'})
        self.assertEqual(IssueChange.objects.filter(issue=self.ticket).count(), 1)
        self.assertFalse(Issue.objects.get(pk=self.ticket.pk).issue_open)

    def test_view_only_user_cannot_change_ticket_status(self):
        self.client.force_login(self.reader)
        response = self.client.post(self.endpoint(), {'action': 'close'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Issue.objects.get(pk=self.ticket.pk).issue_open)
        self.assertFalse(IssueChange.objects.filter(issue=self.ticket).exists())
        queue = self.client.get(reverse('issues:index'))
        self.assertNotContains(queue, 'aria-label="Close ticket')

    def test_unauthenticated_and_get_requests_cannot_change_state(self):
        self.assertEqual(self.client.post(
            self.endpoint(), {'action': 'close'},
        ).status_code, 302)
        self.client.force_login(self.editor)
        self.assertEqual(self.client.get(self.endpoint()).status_code, 405)
        self.assertTrue(Issue.objects.get(pk=self.ticket.pk).issue_open)

    def test_invalid_action_and_missing_ticket_fail_closed(self):
        self.client.force_login(self.editor)
        self.assertEqual(self.client.post(
            self.endpoint(), {'action': 'invalid'},
        ).status_code, 400)
        self.assertEqual(self.client.post(
            reverse('issues:issue_quick_status', args=[self.ticket.pk + 999]),
            {'action': 'close'},
        ).status_code, 404)
        self.assertTrue(Issue.objects.get(pk=self.ticket.pk).issue_open)
        self.assertFalse(IssueChange.objects.filter(issue=self.ticket).exists())

    def test_queue_buttons_and_csrf_token_are_rendered_for_editor(self):
        self.client.force_login(self.editor)
        response = self.client.get(reverse('issues:index'))
        self.assertContains(response, 'aria-label="Close ticket')
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        self.client.post(self.endpoint(), {'action': 'close'})
        response = self.client.get(reverse('issues:index'))
        self.assertContains(response, 'aria-label="Reopen ticket')

    def test_csrf_is_enforced_on_action(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.editor)
        response = client.post(self.endpoint(), {'action': 'close'})
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Issue.objects.get(pk=self.ticket.pk).issue_open)
