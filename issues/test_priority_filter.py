"""Priority filtering across ticket queues and search without permission changes."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority


class TicketPriorityFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = get_user_model().objects.create_user(username='priority-filter-reader')
        cls.other = get_user_model().objects.create_user(username='priority-other')
        cls.operator.user_permissions.add(
            Permission.objects.get(content_type__app_label='issues', codename='view_issue')
        )
        cls.high = Priority.objects.create(name='High')
        cls.normal = Priority.objects.create(name='Normal')
        cls.open_high = Issue.objects.create(
            requestor_name='Alpha', summary='VPN outage', description='Network',
            priority=cls.high, assigned=cls.operator, pub_date=timezone.now(),
        )
        cls.closed_high = Issue.objects.create(
            requestor_name='Beta', summary='VPN recovery', description='Network',
            priority=cls.high, assigned=None, pub_date=timezone.now(), issue_open=False,
        )
        cls.open_normal = Issue.objects.create(
            requestor_name='Gamma', summary='Laptop setup', description='Laptop',
            priority=cls.normal, assigned=cls.other, pub_date=timezone.now(),
        )

    def setUp(self):
        self.client.force_login(self.operator)

    def get_ids(self, route, params):
        response = self.client.get(reverse('issues:' + route), params)
        self.assertEqual(response.status_code, 200)
        return [issue.pk for issue in response.context['issue_list']], response

    def test_priority_filters_all_and_status_queues(self):
        ids, response = self.get_ids('index', {'priority': self.high.pk})
        self.assertEqual(ids, [self.closed_high.pk, self.open_high.pk])
        self.assertEqual(response.context['priority'], str(self.high.pk))
        self.assertContains(response, 'All priorities')
        self.assertContains(response, 'id="ticket-priority"')
        ids, _ = self.get_ids('index', {'priority': self.high.pk, 'status': 'open'})
        self.assertEqual(ids, [self.open_high.pk])
        ids, _ = self.get_ids('index', {'priority': self.high.pk, 'status': 'closed'})
        self.assertEqual(ids, [self.closed_high.pk])

    def test_priority_filter_preserves_assignment_queue_scope(self):
        ids, _ = self.get_ids('my_issues', {'priority': self.high.pk})
        self.assertEqual(ids, [self.open_high.pk])
        ids, _ = self.get_ids('unassigned_issues', {'priority': self.high.pk})
        self.assertEqual(ids, [self.closed_high.pk])
        ids, _ = self.get_ids('my_issues', {'priority': self.normal.pk})
        self.assertEqual(ids, [])

    def test_priority_filter_and_text_search_combine(self):
        ids, response = self.get_ids('search', {
            'q': 'VPN', 'priority': self.high.pk, 'status': 'closed',
        })
        self.assertEqual(ids, [self.closed_high.pk])
        self.assertIn('priority=' + str(self.high.pk), response.context['pagination_query'])
        self.assertIn('status=closed', response.context['pagination_query'])
        self.assertIn('q=VPN', response.context['pagination_query'])
        self.assertContains(response, 'name="priority"')
        self.assertContains(response, 'name="status"')

    def test_invalid_priorities_fail_open_to_unfiltered_view_without_error(self):
        for value in ('not-a-number', '-1', '99999999999', '<script>'):
            ids, response = self.get_ids('index', {'priority': value})
            self.assertEqual(len(ids), 3)
            self.assertEqual(response.context['priority'], '')

    def test_search_keeps_permissions_and_no_query_behavior(self):
        ids, _ = self.get_ids('search', {'priority': self.high.pk})
        self.assertEqual(ids, [])
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse('issues:index'), {'priority': self.high.pk}).status_code,
            302,
        )
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.get(reverse('issues:index'), {'priority': self.high.pk}).status_code,
            403,
        )
