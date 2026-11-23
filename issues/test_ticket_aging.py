"""Open ticket age triage honors existing permissions and queue filters."""
import csv
from datetime import timedelta
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority


class TicketAgeFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reader = get_user_model().objects.create_user(username='age-reader')
        cls.other = get_user_model().objects.create_user(username='age-outsider')
        cls.reader.user_permissions.add(Permission.objects.get(
            content_type__app_label='issues', codename='view_issue',
        ))
        cls.priority = Priority.objects.create(name='High')
        now = timezone.now()
        cls.recent = cls.create_ticket('Recent outage', now - timedelta(hours=8))
        cls.two_days = cls.create_ticket('Two-day outage', now - timedelta(days=2))
        cls.five_days = cls.create_ticket('Five-day outage', now - timedelta(days=5))
        cls.ten_days = cls.create_ticket('Ten-day outage', now - timedelta(days=10))
        cls.closed_old = cls.create_ticket(
            'Closed ten-day case', now - timedelta(days=10), is_open=False,
        )

    @classmethod
    def create_ticket(cls, name, created, is_open=True):
        return Issue.objects.create(
            requestor_name='Fixture', summary=name, description='Incident details',
            priority=cls.priority, assigned=None, issue_open=is_open, pub_date=created,
        )

    def setUp(self):
        self.client.force_login(self.reader)

    def ids(self, route, params):
        response = self.client.get(reverse('issues:' + route), params)
        self.assertEqual(response.status_code, 200)
        return [x.pk for x in response.context['issue_list']], response

    def test_one_three_seven_day_age_thresholds(self):
        for age, expected in (
            ('1', [self.two_days, self.five_days, self.ten_days]),
            ('3', [self.five_days, self.ten_days]),
            ('7', [self.ten_days]),
        ):
            ids, response = self.ids('index', {'age': age})
            self.assertEqual(ids, [x.pk for x in expected])
            self.assertEqual(response.context['age'], age)
            self.assertNotIn(self.closed_old.pk, ids)

    def test_combined_search_priority_and_unassigned_filter(self):
        ids, response = self.ids('search', {
            'q': 'outage', 'age': '3', 'priority': self.priority.pk,
            'assignee': 'unassigned', 'sort': 'oldest', 'status': 'open',
        })
        self.assertEqual(ids, [self.ten_days.pk, self.five_days.pk])
        for item in ('age=3', 'priority=', 'assignee=unassigned',
                     'sort=oldest', 'status=open', 'q=outage'):
            self.assertIn(item, response.context['pagination_query'])
        self.assertContains(response, 'id="ticket-age"')

    def test_age_and_closed_status_return_empty(self):
        ids, _ = self.ids('index', {'age': '1', 'status': 'closed'})
        self.assertEqual(ids, [])

    def test_invalid_age_is_not_applied_or_echoed_as_selected(self):
        for value in ('-1', '0', '1000', '<script>', '3.0'):
            ids, response = self.ids('index', {'age': value})
            self.assertEqual(len(ids), 5)
            self.assertEqual(response.context['age'], '')

    def test_csv_export_has_same_age_scope_and_sort(self):
        params = {'age': '3', 'sort': 'oldest'}
        ids, response = self.ids('index', params)
        self.assertContains(response, 'age=3')
        exported = self.client.get(reverse('issues:index'), {
            **params, 'export': 'csv', 'page': 99,
        })
        rows = list(csv.reader(StringIO(
            b''.join(exported.streaming_content).decode('utf-8')
        )))
        self.assertEqual([int(row[0]) for row in rows[1:]], ids)
        self.assertEqual(len(rows), 3)

    def test_empty_selection_has_clear_options_and_no_results(self):
        response = self.client.get(reverse('issues:search'), {
            'q': 'never found', 'age': '7',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Older than 7 days')
        self.assertContains(response, 'No issues are available.')

    def test_age_filter_does_not_bypass_authentication_or_permissions(self):
        self.client.logout()
        self.assertEqual(self.client.get(
            reverse('issues:index'), {'age': '7'},
        ).status_code, 302)
        self.client.force_login(self.other)
        for params in ({'age': '7'}, {'age': '7', 'export': 'csv'}):
            self.assertEqual(self.client.get(
                reverse('issues:index'), params,
            ).status_code, 403)
