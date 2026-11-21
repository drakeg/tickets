"""Stable user-controlled queue and CSV ordering."""
import csv
from io import StringIO

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from issues.models import Issue, Priority


class TicketQueueOrderingTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.reader = get_user_model().objects.create_user(username='sort-reader')
        cls.other = get_user_model().objects.create_user(username='sort-other')
        cls.reader.user_permissions.add(
            Permission.objects.get(content_type__app_label='issues', codename='view_issue')
        )
        priority = Priority.objects.create(name='High')
        timestamp = timezone.now()
        cls.tickets = [
            Issue.objects.create(
                requestor_name='Fixture', summary=f'Network ticket {number}',
                description='Network', priority=priority, pub_date=timestamp,
                assigned=cls.reader if number % 2 else cls.other,
                issue_open=number % 3 != 0,
            )
            for number in range(35)
        ]

    def setUp(self):
        self.client.force_login(self.reader)

    def test_oldest_first_paginates_all_without_skips_or_repeats(self):
        collected = []
        for number in (1, 2, 3):
            response = self.client.get(reverse('issues:index'), {
                'sort': 'oldest', 'page': number,
            })
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['sort'], 'oldest')
            collected.extend(ticket.pk for ticket in response.context['issue_list'])
        self.assertEqual(collected, [ticket.pk for ticket in self.tickets])
        self.assertEqual(len(set(collected)), len(self.tickets))

    def test_default_newest_and_invalid_sort_are_safe(self):
        expected = [ticket.pk for ticket in reversed(self.tickets)]
        for params in ({}, {'sort': 'not-a-sort'}, {'sort': '<script>'}):
            response = self.client.get(reverse('issues:index'), params)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['sort'], 'newest')
            self.assertEqual(
                [ticket.pk for ticket in response.context['issue_list']],
                expected[:15],
            )

    def test_oldest_with_status_and_assignment_scope(self):
        response = self.client.get(reverse('issues:my_issues'), {
            'sort': 'oldest', 'status': 'open',
        })
        expected = [
            ticket.pk for ticket in self.tickets
            if ticket.assigned_id == self.reader.pk and ticket.issue_open
        ]
        self.assertEqual(
            [ticket.pk for ticket in response.context['issue_list']], expected[:15]
        )
        self.assertContains(response, 'sort=oldest')
        self.assertContains(response, 'id="ticket-sort"')

    def test_csv_order_matches_queue_order_and_ignores_page(self):
        url = reverse('issues:search')
        params = {'q': 'Network', 'sort': 'oldest', 'status': 'open'}
        response = self.client.get(url, params)
        self.assertEqual(response.status_code, 200)
        queue = [ticket.pk for ticket in response.context['issue_list']]
        self.assertEqual(queue, [
            ticket.pk for ticket in self.tickets if ticket.issue_open
        ][:15])
        download = self.client.get(url, {**params, 'page': 3, 'export': 'csv'})
        rows = list(csv.reader(StringIO(
            b''.join(download.streaming_content).decode('utf-8')
        )))
        actual = [int(row[0]) for row in rows[1:]]
        expected = [ticket.pk for ticket in self.tickets if ticket.issue_open]
        self.assertEqual(actual, expected)

    def test_search_form_keeps_oldest_sort_and_filters(self):
        response = self.client.get(reverse('issues:search'), {
            'q': 'Network', 'sort': 'oldest',
        })
        self.assertContains(response, 'name="sort" value="oldest"')
        self.assertContains(response, 'sort=oldest')

    def test_unprivileged_users_cannot_read_or_export_sorted_data(self):
        self.client.logout()
        self.assertEqual(self.client.get(
            reverse('issues:index'), {'sort': 'oldest'},
        ).status_code, 302)
        self.client.force_login(self.other)
        for params in ({'sort': 'oldest'}, {'sort': 'oldest', 'export': 'csv'}):
            self.assertEqual(
                self.client.get(reverse('issues:index'), params).status_code, 403
            )
