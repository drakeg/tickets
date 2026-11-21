"""Ticket queue search across requesters, assignees, priorities and text."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority


class TicketRelatedSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reader = get_user_model().objects.create_user(username='ticket-search-reader')
        cls.reader.user_permissions.add(Permission.objects.get(codename='view_issue'))
        cls.unprivileged = get_user_model().objects.create_user(
            username='ticket-search-unprivileged',
        )
        cls.amy = get_user_model().objects.create_user(username='support-amy')
        cls.ben = get_user_model().objects.create_user(username='support-ben')
        high = Priority.objects.create(name='High urgency')
        normal = Priority.objects.create(name='Normal')
        cls.first = Issue.objects.create(
            requestor_name='Alice Customer', summary='VPN problem',
            description='Remote connectivity fails', priority=high,
            assigned=cls.amy, pub_date=timezone.now(),
        )
        cls.second = Issue.objects.create(
            requestor_name='Bob Customer', summary='Laptop setup',
            description='First-day onboarding', priority=normal,
            assigned=cls.ben, pub_date=timezone.now(), issue_open=False,
        )
        cls.third = Issue.objects.create(
            requestor_name='Carol Customer', summary='High uptime alert',
            description='Monitoring warning', priority=normal,
            assigned=None, pub_date=timezone.now(),
        )

    def setUp(self):
        self.client.force_login(self.reader)

    def search(self, query, **other):
        response = self.client.get(reverse('issues:search'), {'q': query, **other})
        self.assertEqual(response.status_code, 200)
        return [issue.pk for issue in response.context['issue_list']], response

    def test_search_matches_requester_assignee_priority_and_ticket_text(self):
        for query, expected in (
            ('alice', [self.first]),
            ('support-ben', [self.second]),
            ('urgency', [self.first]),
            ('VPN', [self.first]),
            ('onboarding', [self.second]),
            ('high', [self.first, self.third]),
        ):
            actual, _ = self.search(query)
            self.assertEqual(actual, sorted(
                (issue.pk for issue in expected), reverse=True,
            ), query)

    def test_search_result_remains_unique_with_multiple_matching_fields(self):
        ids, _ = self.search('high')
        self.assertEqual(ids.count(self.first.pk), 1)
        self.assertEqual(len(ids), 2)

    def test_status_filter_and_search_query_survive_pagination_context(self):
        ids, response = self.search('Customer', status='closed')
        self.assertEqual(ids, [self.second.pk])
        self.assertEqual(response.context['status'], 'closed')
        self.assertIn('q=Customer', response.context['pagination_query'])
        self.assertIn('status=closed', response.context['pagination_query'])

    def test_query_field_escapes_user_input_and_shows_search_hint(self):
        _, response = self.search('Alice & Bob')
        self.assertContains(
            response,
            'Search tickets by summary, description, requester, assignee or priority',
        )
        self.assertContains(response, 'Alice &amp; Bob')
        self.assertNotContains(response, 'value="Alice & Bob"')

    def test_blank_and_unmatched_queries_show_no_private_tickets(self):
        for query in ('', '   ', 'not-present-anywhere'):
            ids, response = self.search(query)
            self.assertEqual(ids, [])
            self.assertContains(response, 'No issues are available.')

    def test_search_keeps_authentication_and_permission_gate(self):
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse('issues:search'), {'q': 'Alice'}).status_code,
            302,
        )
        self.client.force_login(self.unprivileged)
        self.assertEqual(
            self.client.get(reverse('issues:search'), {'q': 'Alice'}).status_code,
            403,
        )
