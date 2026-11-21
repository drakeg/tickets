"""Verify useful, accessible ticket queue cells for agents."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority


class QueueReadabilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reader = get_user_model().objects.create_user(username='queue-reader')
        cls.reader.user_permissions.add(
            Permission.objects.get(content_type__app_label='issues', codename='view_issue')
        )
        cls.agent = get_user_model().objects.create_user(username='queue-agent')
        cls.priority = Priority.objects.create(name='High')
        cls.open_ticket = Issue.objects.create(
            requestor_name='Requester A',
            summary='Printer is offline',
            description='Detailed internal notes',
            priority=cls.priority,
            assigned=cls.agent,
            issue_open=True,
            pub_date=timezone.now(),
        )
        cls.closed_ticket = Issue.objects.create(
            requestor_name='Requester B',
            summary='VPN access solved',
            description='More internal notes',
            priority=cls.priority,
            assigned=None,
            issue_open=False,
            pub_date=timezone.now(),
        )

    def setUp(self):
        self.client.force_login(self.reader)

    def test_queue_shows_linked_summary_priority_assignee_and_status_text(self):
        response = self.client.get(reverse('issues:index'))
        self.assertEqual(response.status_code, 200)
        for header in ('Summary', 'Priority', 'Status', 'Requestor'):
            self.assertContains(response, header)
        for summary, ticket in (
            ('Printer is offline', self.open_ticket),
            ('VPN access solved', self.closed_ticket),
        ):
            self.assertContains(
                response,
                '<a href="{}">{}</a>'.format(
                    reverse('issues:issue', args=[ticket.pk]), summary
                ),
                html=True,
            )
        self.assertContains(response, 'High', count=2)
        self.assertContains(response, 'queue-agent')
        self.assertContains(response, 'Unassigned')
        self.assertContains(response, 'Open')
        self.assertContains(response, 'Closed')
        self.assertNotContains(response, 'type="checkbox"')
        self.assertNotContains(response, 'Detailed internal notes')

    def test_filtered_search_queue_renders_same_fields_without_leak(self):
        response = self.client.get(
            reverse('issues:search'), {'q': 'VPN', 'status': 'closed'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'VPN access solved')
        self.assertContains(response, 'Unassigned')
        self.assertContains(response, 'Closed')
        self.assertNotContains(response, 'Printer is offline')
        self.assertEqual(response.context['page_obj'].paginator.count, 1)

    def test_html_special_characters_in_summary_are_escaped(self):
        unsafe = Issue.objects.create(
            requestor_name='safe', summary='<img src=x onerror=alert(1)>',
            description='fixture', priority=self.priority,
            pub_date=timezone.now(),
        )
        response = self.client.get(reverse('issues:index'))
        self.assertContains(response, '&lt;img src=x onerror=alert(1)&gt;')
        self.assertNotContains(response, '<img src=x onerror=alert(1)>')
        self.assertContains(response, reverse('issues:issue', args=[unsafe.pk]))

    def test_permission_requirement_still_hides_queue(self):
        self.client.logout()
        response = self.client.get(reverse('issues:index'))
        self.assertEqual(response.status_code, 302)
        unprivileged = get_user_model().objects.create_user(username='no-tickets')
        self.client.force_login(unprivileged)
        self.assertEqual(self.client.get(reverse('issues:index')).status_code, 403)
