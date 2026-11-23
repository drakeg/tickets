"""Actionable unassigned-ticket metric is permission-gated and scope-correct."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority


class UnassignedDashboardMetricTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reader = get_user_model().objects.create_user(username='unassigned-kpi-reader')
        cls.other = get_user_model().objects.create_user(username='unassigned-kpi-noaccess')
        cls.reader.user_permissions.add(Permission.objects.get(
            content_type__app_label='issues', codename='view_issue',
        ))
        priority = Priority.objects.create(name='Normal')
        for label, open_, assignee in (
            ('Unclaimed outage', True, None),
            ('Unclaimed access', True, None),
            ('Resolved outage', False, None),
            ('Taken issue', True, cls.reader),
        ):
            Issue.objects.create(
                requestor_name='Fixture', summary=label,
                description='Synthetic', issue_open=open_,
                priority=priority, assigned=assignee,
                pub_date=timezone.now(),
            )

    def test_count_and_drilldown_match_unassigned_open_queue(self):
        self.client.force_login(self.reader)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['num_unassigned_open'], 2)
        self.assertContains(response, 'Unassigned open tickets')
        self.assertContains(response, 'status=open')
        self.assertContains(response, reverse('issues:unassigned_issues'))
        listing = self.client.get(reverse('issues:unassigned_issues'), {
            'status': 'open',
        })
        self.assertEqual(listing.context['page_obj'].paginator.count, 2)

    def test_without_ticket_permission_no_count_or_card_is_exposed(self):
        self.client.force_login(self.other)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['num_unassigned_open'], 0)
        self.assertNotContains(response, 'Unassigned open tickets')

    def test_reassigning_ticket_updates_count_without_stale_cache(self):
        ticket = Issue.objects.get(summary='Unclaimed outage')
        ticket.assigned = self.reader
        ticket.save(update_fields=['assigned'])
        self.client.force_login(self.reader)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.context['num_unassigned_open'], 1)
