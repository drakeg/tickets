"""Permission-scoped CSV export of filtered ticket queues."""
import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority


class TicketCSVExportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reader = get_user_model().objects.create_user(username='csv-reader')
        cls.agent = get_user_model().objects.create_user(username='csv-agent')
        cls.other = get_user_model().objects.create_user(username='csv-other')
        cls.reader.user_permissions.add(
            Permission.objects.get(content_type__app_label='issues', codename='view_issue')
        )
        cls.agent.user_permissions.add(
            Permission.objects.get(content_type__app_label='issues', codename='view_issue')
        )
        cls.high = Priority.objects.create(name='High')
        cls.low = Priority.objects.create(name='Low')
        cls.first = Issue.objects.create(
            requestor_name='A & B', summary='VPN outage',
            description='Network is unavailable', priority=cls.high,
            assigned=cls.agent, issue_open=True, pub_date=timezone.now(),
        )
        cls.second = Issue.objects.create(
            requestor_name='Other', summary='Closed setup',
            description='Finished setup', priority=cls.low,
            assigned=None, issue_open=False, pub_date=timezone.now(),
        )
        cls.third = Issue.objects.create(
            requestor_name='Third', summary='Monitor network',
            description='Check alerts', priority=cls.high,
            assigned=cls.other, issue_open=True, pub_date=timezone.now(),
        )

    def setUp(self):
        self.client.force_login(self.reader)

    def csv_rows(self, route='index', **params):
        response = self.client.get(reverse('issues:' + route), {'export': 'csv', **params})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.streaming)
        self.assertIn('text/csv', response['Content-Type'])
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertEqual(response['Cache-Control'], 'private, no-store')
        body = b''.join(response.streaming_content).decode('utf-8')
        return list(csv.reader(StringIO(body)))

    def test_all_export_contains_expected_fields_and_stable_order(self):
        rows = self.csv_rows()
        self.assertEqual(rows[0], [
            'Ticket ID', 'Summary', 'Requestor', 'Description', 'Priority',
            'Assignee', 'Status', 'Created (ISO 8601)',
        ])
        self.assertEqual([int(row[0]) for row in rows[1:]], [
            self.third.pk, self.second.pk, self.first.pk,
        ])
        self.assertEqual(rows[-1][1:7], [
            'VPN outage', 'A & B', 'Network is unavailable',
            'High', 'csv-agent', 'Open',
        ])
        self.assertEqual(rows[2][5], 'Unassigned')
        self.assertEqual(rows[2][6], 'Closed')

    def test_filters_and_search_scopes_match_on_screen_queue(self):
        rows = self.csv_rows(
            'search', q='Network', status='open', priority=self.high.pk,
            assignee=self.agent.pk,
        )
        self.assertEqual([int(row[0]) for row in rows[1:]], [self.first.pk])
        rows = self.csv_rows('unassigned_issues', status='closed')
        self.assertEqual([int(row[0]) for row in rows[1:]], [self.second.pk])
        self.client.force_login(self.agent)
        rows = self.csv_rows('my_issues')
        self.assertEqual([int(row[0]) for row in rows[1:]], [self.first.pk])

    def test_export_is_not_limited_to_visible_paginated_page(self):
        for number in range(22):
            Issue.objects.create(
                requestor_name='Sample', summary=f'Batch item {number}',
                description='More', priority=self.low,
                pub_date=timezone.now(),
            )
        rows = self.csv_rows(page=1)
        self.assertEqual(len(rows), 26)

    def test_formula_prefixes_are_escaped_without_mangling_normal_text(self):
        for number, value in enumerate((
            '=SUM(1,1)', '+cmd', '-cmd', '@NOW()', ' \t=1+1',
        )):
            Issue.objects.create(
                requestor_name=value, summary=f'Unsafe {number}',
                description=value, priority=self.low, pub_date=timezone.now(),
            )
        rows = self.csv_rows()
        unsafe = [row for row in rows[1:] if row[1].startswith('Unsafe ')]
        self.assertEqual(len(unsafe), 5)
        for row in unsafe:
            self.assertTrue(row[2].startswith("'"), row)
            self.assertTrue(row[3].startswith("'"), row)
        self.assertEqual(
            next(row for row in rows[1:] if row[1] == 'VPN outage')[2],
            'A & B',
        )

    def test_queue_link_preserves_filters_but_drops_page(self):
        response = self.client.get(reverse('issues:search'), {
            'q': 'VPN', 'priority': self.high.pk,
            'assignee': self.agent.pk, 'page': 4,
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'export=csv')
        self.assertContains(response, 'q=VPN')
        self.assertContains(response, 'priority=' + str(self.high.pk))
        self.assertContains(response, 'assignee=' + str(self.agent.pk))
        self.assertNotContains(response, 'page=4&amp;export=csv')

    def test_read_permission_required_for_export(self):
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse('issues:index'), {'export': 'csv'}).status_code,
            302,
        )
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.get(reverse('issues:index'), {'export': 'csv'}).status_code,
            403,
        )
