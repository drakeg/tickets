"""Open-ticket aging dashboard cards obey RBAC and match ticket filters."""
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority


class AgingDashboardKPITests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reader = get_user_model().objects.create_user(username='age-metric-reader')
        cls.restricted = get_user_model().objects.create_user(username='age-metric-hidden')
        cls.reader.user_permissions.add(Permission.objects.get(
            content_type__app_label='issues', codename='view_issue',
        ))
        priority = Priority.objects.create(name='Normal')
        now = timezone.now()
        for index, (days, open_) in enumerate((
            (1, True), (4, True), (9, True), (15, False),
        )):
            Issue.objects.create(
                requestor_name='Fixture',
                summary=f'Age KPI sample {index}',
                description='Synthetic ticket',
                priority=priority,
                pub_date=now - timedelta(days=days),
                issue_open=open_,
            )

    def test_aging_counts_exclude_closed_and_link_to_queue(self):
        self.client.force_login(self.reader)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['num_aging_3_days'], 2)
        self.assertEqual(response.context['num_aging_7_days'], 1)
        self.assertContains(response, 'Open over 3 days')
        self.assertContains(response, '1 over 7 days')
        self.assertContains(response, 'status=open&amp;age=3')
        filtered = self.client.get(reverse('issues:index'), {
            'status': 'open', 'age': '3',
        })
        self.assertEqual(filtered.context['page_obj'].paginator.count, 2)

    def test_metrics_are_not_rendered_for_user_without_ticket_grant(self):
        self.client.force_login(self.restricted)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['num_aging_3_days'], 0)
        self.assertEqual(response.context['num_aging_7_days'], 0)
        self.assertNotContains(response, 'Open over 3 days')
        self.assertNotContains(response, 'status=open&amp;age=3')

    def test_closed_and_recent_tickets_do_not_count_as_aging(self):
        Issue.objects.filter(issue_open=True).update(
            pub_date=timezone.now() - timedelta(hours=2),
        )
        self.client.force_login(self.reader)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.context['num_aging_3_days'], 0)
        self.assertEqual(response.context['num_aging_7_days'], 0)
