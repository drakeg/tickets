"""Assignee filter behavior across permissioned ticket queues."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority


class TicketAssigneeFilterTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.agent_a = get_user_model().objects.create_user(username='agent-alpha')
        cls.agent_b = get_user_model().objects.create_user(username='agent-beta')
        cls.reader = get_user_model().objects.create_user(username='assignee-reader')
        cls.reader.user_permissions.add(
            Permission.objects.get(content_type__app_label='issues', codename='view_issue')
        )
        cls.unrelated_user = get_user_model().objects.create_user(username='unrelated-user')
        cls.high = Priority.objects.create(name='High')
        cls.low = Priority.objects.create(name='Low')
        cls.first = Issue.objects.create(
            requestor_name='User A', summary='Network alpha',
            description='Network', priority=cls.high, assigned=cls.agent_a,
            pub_date=timezone.now(),
        )
        cls.second = Issue.objects.create(
            requestor_name='User B', summary='Network beta',
            description='Network', priority=cls.low, assigned=cls.agent_b,
            pub_date=timezone.now(), issue_open=False,
        )
        cls.third = Issue.objects.create(
            requestor_name='User C', summary='Network unassigned',
            description='Network', priority=cls.high, assigned=None,
            pub_date=timezone.now(),
        )

    def setUp(self):
        self.client.force_login(self.reader)

    def query(self, route='index', **params):
        response = self.client.get(reverse('issues:' + route), params)
        self.assertEqual(response.status_code, 200)
        return [issue.pk for issue in response.context['issue_list']], response

    def test_filter_by_specific_agent_and_unassigned(self):
        ids, response = self.query(assignee=str(self.agent_a.pk))
        self.assertEqual(ids, [self.first.pk])
        self.assertEqual(response.context['assignee'], str(self.agent_a.pk))
        self.assertContains(response, 'id="ticket-assignee"')
        ids, _ = self.query(assignee=str(self.agent_b.pk))
        self.assertEqual(ids, [self.second.pk])
        ids, _ = self.query(assignee='unassigned')
        self.assertEqual(ids, [self.third.pk])

    def test_assignee_combines_with_priority_status_and_search(self):
        ids, response = self.query(
            'search', q='Network', status='open',
            priority=str(self.high.pk), assignee=str(self.agent_a.pk),
        )
        self.assertEqual(ids, [self.first.pk])
        for key, value in (
            ('q', 'Network'), ('status', 'open'),
            ('priority', str(self.high.pk)), ('assignee', str(self.agent_a.pk)),
        ):
            self.assertIn(key + '=' + value, response.context['pagination_query'])
        self.assertContains(response, 'name="assignee"')
        ids, _ = self.query(
            'search', q='Network', priority=str(self.high.pk),
            assignee='unassigned',
        )
        self.assertEqual(ids, [self.third.pk])

    def test_assignment_specific_queues_keep_original_scope(self):
        self.client.force_login(self.agent_a)
        self.agent_a.user_permissions.add(
            Permission.objects.get(content_type__app_label='issues', codename='view_issue')
        )
        ids, _ = self.query('my_issues', assignee=str(self.agent_b.pk))
        # Unknown agents for this scoped queue are ignored, never broadening it.
        self.assertEqual(ids, [self.first.pk])
        ids, response = self.query('my_issues', assignee=str(self.agent_a.pk))
        self.assertEqual(ids, [self.first.pk])
        self.assertNotContains(response, 'agent-beta')
        ids, _ = self.query('unassigned_issues', assignee='unassigned')
        self.assertEqual(ids, [self.third.pk])

    def test_unknown_and_oversized_assignee_are_ignored_without_error(self):
        for value in ('nonexistent', '-1', '99999999999999999999999999999', str(self.unrelated_user.pk)):
            ids, response = self.query(assignee=value)
            self.assertEqual(len(ids), 3)
            self.assertEqual(response.context['assignee'], '')

    def test_only_assigned_usernames_are_offered_as_choices(self):
        _, response = self.query()
        self.assertContains(response, 'agent-alpha')
        self.assertContains(response, 'agent-beta')
        self.assertNotContains(response, 'unrelated-user')
        self.assertContains(response, 'All agents')

    def test_permission_gate_preserved_for_assignment_filters(self):
        self.client.logout()
        self.assertEqual(self.client.get(
            reverse('issues:index'), {'assignee': self.agent_a.pk},
        ).status_code, 302)
        self.client.force_login(self.unrelated_user)
        self.assertEqual(self.client.get(
            reverse('issues:index'), {'assignee': self.agent_a.pk},
        ).status_code, 403)
