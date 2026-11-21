"""Ticket history CSV must remain scoped to ticket editors."""
import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, IssueChange, Priority


class TicketHistoryCSVTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.editor = get_user_model().objects.create_user(username='history-editor')
        cls.reader = get_user_model().objects.create_user(username='history-reader')
        cls.outsider = get_user_model().objects.create_user(username='history-outsider')
        cls.editor.user_permissions.add(*Permission.objects.filter(
            content_type__app_label='issues',
            codename__in=('view_issue', 'change_issue'),
        ))
        cls.reader.user_permissions.add(Permission.objects.get(
            content_type__app_label='issues', codename='view_issue',
        ))
        priority = Priority.objects.create(name='Normal')
        cls.issue = Issue.objects.create(
            requestor_name='Alice', summary='Password reset',
            description='Account issue', priority=priority,
            pub_date=timezone.now(), assigned=cls.editor,
        )
        cls.other_issue = Issue.objects.create(
            requestor_name='Bob', summary='Other ticket',
            description='Private other ticket', priority=priority,
            pub_date=timezone.now(),
        )
        before = {
            'status': 'Open',
            'priority': {'id': priority.pk, 'name': 'Normal'},
            'assigned': {'id': cls.editor.pk, 'name': 'history-editor'},
        }
        after = {
            'status': 'Closed',
            'priority': {'id': priority.pk, 'name': '=MALICIOUS()'},
            'assigned': {'id': None, 'name': '@cmd'},
        }
        cls.change = IssueChange.objects.create(
            issue=cls.issue, actor=cls.editor,
            actor_name='+history-editor', before=before, after=after,
        )
        IssueChange.objects.create(
            issue=cls.other_issue, actor=cls.editor,
            actor_name='other-actor', before=before, after=after,
        )

    def setUp(self):
        self.client.force_login(self.editor)

    def url(self, ticket=None):
        return reverse('issues:issue_history_csv', args=[
            ticket.pk if ticket else self.issue.pk,
        ])

    def read_csv(self):
        response = self.client.get(self.url())
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        self.assertIn('attachment', response['Content-Disposition'])
        content = b''.join(response.streaming_content).decode('utf-8')
        return list(csv.reader(StringIO(content)))

    def test_exports_only_target_history_and_preserves_before_after(self):
        rows = self.read_csv()
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], [
            'Ticket ID', 'Changed (ISO 8601)', 'Actor',
            'Previous status', 'New status', 'Previous priority', 'New priority',
            'Previous assignee', 'New assignee',
        ])
        self.assertEqual(rows[1][0], str(self.issue.pk))
        self.assertEqual(rows[1][3:5], ['Open', 'Closed'])
        self.assertNotIn('other-actor', str(rows))

    def test_injected_formula_fields_are_escaped(self):
        row = self.read_csv()[1]
        self.assertEqual(row[2], "'+history-editor")
        self.assertEqual(row[6], "'=MALICIOUS()")
        self.assertEqual(row[8], "'@cmd")

    def test_readonly_user_can_view_ticket_not_history_export(self):
        self.client.force_login(self.reader)
        self.assertEqual(self.client.get(self.url()).status_code, 403)
        detail = self.client.get(reverse('issues:issue', args=[self.issue.pk]))
        self.assertEqual(detail.status_code, 200)
        self.assertNotContains(detail, 'Export change history CSV')

    def test_anonymous_and_no_role_users_are_denied(self):
        self.client.logout()
        self.assertEqual(self.client.get(self.url()).status_code, 302)
        self.client.force_login(self.outsider)
        self.assertEqual(self.client.get(self.url()).status_code, 403)

    def test_export_link_visible_to_authorized_editor(self):
        detail = self.client.get(reverse('issues:issue', args=[self.issue.pk]))
        self.assertContains(detail, 'Export change history CSV')
        self.assertContains(detail, self.url())

    def test_missing_ticket_and_other_ticket_history(self):
        missing = reverse('issues:issue_history_csv', args=[self.issue.pk + 9999])
        self.assertEqual(self.client.get(missing).status_code, 404)
        response = self.client.get(self.url(self.other_issue))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(list(csv.reader(StringIO(
            b''.join(response.streaming_content).decode('utf-8')
        )))), 2)
