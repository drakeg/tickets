from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Issue, Priority


class IssueWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="issue-user",
            password="test-password",
        )
        self.priority = Priority.objects.create(name="Normal")
        self.issue = Issue.objects.create(
            requestor_name="issue-user",
            summary="Printer unavailable",
            description="Office printer is offline",
            priority=self.priority,
            pub_date=timezone.now(),
            assigned=self.user,
        )

    def test_issue_detail_returns_requested_issue(self):
        response = self.client.get(reverse("issues:issue", args=[self.issue.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["issue"], self.issue)

    def test_issue_search_matches_summary_or_description(self):
        response = self.client.get(reverse("issues:search"), {"q": "printer"})

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["issue_list"],
            [self.issue],
            transform=lambda issue: issue,
        )

    def test_empty_issue_search_returns_empty_result(self):
        response = self.client.get(reverse("issues:search"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["issue_list"]), [])

    def test_issue_create_requires_authentication(self):
        response = self.client.get(reverse("issues:issue_new"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_my_issues_requires_authentication(self):
        response = self.client.get(reverse("issues:my_issues"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_issue_form_creates_issue(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("issues:issue_new"),
            {
                "summary": "VPN access",
                "description": "Unable to connect to VPN",
                "priority": self.priority.pk,
                "assigned": self.user.pk,
            },
        )

        created = Issue.objects.get(summary="VPN access")
        self.assertEqual(created.requestor_name, self.user.username)
        self.assertEqual(created.assigned, self.user)

        self.assertRedirects(
            response, reverse("issues:issue", args=[created.pk])
        )
        self.client.get(response["Location"])
        self.assertEqual(Issue.objects.filter(summary="VPN access").count(), 1)

    def test_invalid_submission_keeps_errors_and_does_not_create_ticket(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("issues:issue_new"),
            {"summary": "", "description": "Keep this text", "priority": self.priority.pk},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context["form"], "summary", "This field is required.")
        self.assertContains(response, "Keep this text")
        self.assertEqual(Issue.objects.count(), 1)

    def test_detail_displays_ticket_fields(self):
        response = self.client.get(reverse("issues:issue", args=[self.issue.pk]))
        for value in ("Printer unavailable", "Office printer is offline", "Normal", "Open", "issue-user"):
            self.assertContains(response, value)
        self.assertContains(response, reverse("issues:index"))

    def test_detail_displays_closed_unassigned_ticket_and_escapes_description(self):
        self.issue.issue_open = False
        self.issue.assigned = None
        self.issue.description = '<script>alert("unsafe")</script>\nSecond line'
        self.issue.save()
        response = self.client.get(reverse("issues:issue", args=[self.issue.pk]))
        self.assertContains(response, "Closed")
        self.assertContains(response, "Unassigned")
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("unsafe")</script>')
        self.assertContains(response, "<br>Second line")

    def test_missing_ticket_returns_404(self):
        response = self.client.get(reverse("issues:issue", args=[self.issue.pk + 1]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_submission_cannot_create_ticket(self):
        response = self.client.post(reverse("issues:issue_new"), {
            "summary": "Unauthorized", "description": "Blocked", "priority": self.priority.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])
        self.assertEqual(Issue.objects.count(), 1)


class IssueQueueTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='queue-user')
        cls.other = get_user_model().objects.create_user(username='other-user')
        priority = Priority.objects.create(name='Normal')
        now = timezone.now()
        cls.tickets = [Issue.objects.create(
            requestor_name='requestor', summary=f'Network {number}',
            description='Network & access', priority=priority, pub_date=now,
            assigned=cls.user if number % 2 else None,
            issue_open=number % 3 != 0,
        ) for number in range(34)]
        cls.foreign = Issue.objects.create(
            requestor_name='other', summary='Other queue', description='Other',
            priority=priority, pub_date=now, assigned=cls.other,
        )

    def test_all_tickets_are_reachable_with_stable_newest_first_order(self):
        ids = []
        for number in (1, 2, 3):
            response = self.client.get(reverse('issues:index'), {'page': number})
            self.assertEqual(response.status_code, 200)
            ids.extend(issue.pk for issue in response.context['issue_list'])
        expected = list(Issue.objects.order_by('-pub_date', '-pk').values_list('pk', flat=True))
        self.assertEqual(ids, expected)
        self.assertEqual(len(ids), len(set(ids)))

    def test_status_filters_and_invalid_status_fallback(self):
        for status, expected in [('open', True), ('closed', False)]:
            response = self.client.get(reverse('issues:index'), {'status': status})
            self.assertEqual(response.context['page_obj'].paginator.count,
                             Issue.objects.filter(issue_open=expected).count())
            self.assertTrue(all(i.issue_open == expected for i in response.context['issue_list']))
        response = self.client.get(reverse('issues:index'), {'status': 'invalid'})
        self.assertEqual(response.context['status'], 'all')
        self.assertEqual(response.context['page_obj'].paginator.count, Issue.objects.count())

    def test_assignment_queues_keep_scope_when_filtering_and_paging(self):
        self.client.force_login(self.user)
        for route, filters in [('my_issues', {'assigned': self.user}),
                               ('unassigned_issues', {'assigned__isnull': True})]:
            response = self.client.get(reverse('issues:' + route), {'status': 'open', 'page': 2})
            expected = Issue.objects.filter(issue_open=True, **filters)
            self.assertEqual(response.context['page_obj'].paginator.count, expected.count())
            self.assertTrue(set(response.context['issue_list']).issubset(set(expected)))
            self.assertNotIn(self.foreign, response.context['issue_list'])

    def test_search_pagination_preserves_query_and_status(self):
        response = self.client.get(reverse('issues:search'), {'q': 'Network &', 'status': 'open'})
        self.assertContains(response, 'q=Network+%26')
        self.assertContains(response, 'status=open')
        self.assertContains(response, 'page=2')
        response = self.client.get(reverse('issues:search'), {
            'q': 'Network &', 'status': 'open', 'page': 2,
        })
        self.assertTrue(response.context['issue_list'])
        self.assertTrue(all(i.issue_open and 'Network &' in i.description
                            for i in response.context['issue_list']))

    def test_invalid_page_numbers_fall_back_safely(self):
        for value, expected in [('bad', 1), ('999', 3), ('0', 3), ('-1', 3)]:
            response = self.client.get(reverse('issues:index'), {'page': value})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.context['page_obj'].number, expected)

    def test_empty_search_and_closed_navigation(self):
        response = self.client.get(reverse('issues:search'), {'q': '   ', 'page': 99})
        self.assertContains(response, 'No issues are available.')
        self.assertEqual(response.context['page_obj'].paginator.count, 0)
        self.assertContains(response, reverse('issues:index') + '?status=closed')


class IssueTriageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Permission
        cls.agent = get_user_model().objects.create_user(username='agent')
        cls.agent.user_permissions.add(Permission.objects.get(
            content_type__app_label='issues', codename='change_issue'))
        cls.other = get_user_model().objects.create_user(username='unprivileged', is_staff=True)
        cls.priority = Priority.objects.create(name='Normal')
        cls.urgent = Priority.objects.create(name='Urgent')
        cls.issue = Issue.objects.create(
            requestor_name='requestor', summary='Preserve summary', description='Preserve description',
            priority=cls.priority, pub_date=timezone.now(), assigned=cls.other,
        )

    def setUp(self):
        self.url = reverse('issues:issue_edit', args=[self.issue.pk])
        self.payload = {'issue_open': 'closed', 'priority': self.urgent.pk, 'assigned': self.agent.pk}

    def test_permission_required_for_get_and_post_even_for_staff_or_assignee(self):
        for method in (self.client.get, self.client.post):
            response = method(self.url, self.payload)
            self.assertEqual(response.status_code, 302)
            self.assertIn(reverse('login'), response['Location'])
        self.client.force_login(self.other)
        self.assertEqual(self.client.get(self.url).status_code, 403)
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 403)
        self.issue.refresh_from_db()
        self.assertTrue(self.issue.issue_open)
        self.assertEqual(self.issue.priority, self.priority)

    def test_agent_can_close_reopen_and_unassign_without_changing_content(self):
        self.client.force_login(self.agent)
        before_date = self.issue.pub_date
        self.payload.update(summary='Tampered', requestor_name='Tampered', description='Tampered')
        for status, assigned in [('closed', self.agent.pk), ('open', ''), ('open', '')]:
            self.payload.update(issue_open=status, assigned=assigned)
            response = self.client.post(self.url, self.payload)
            self.assertRedirects(response, reverse('issues:issue', args=[self.issue.pk]))
            self.issue.refresh_from_db()
            self.assertEqual(self.issue.issue_open, status == 'open')
            self.assertEqual(self.issue.assigned_id, assigned or None)
            self.assertEqual(self.issue.priority, self.urgent)
            self.assertEqual(self.issue.summary, 'Preserve summary')
            self.assertEqual(self.issue.description, 'Preserve description')
            self.assertEqual(self.issue.requestor_name, 'requestor')
            self.assertEqual(self.issue.pub_date, before_date)

    def test_get_is_read_only_and_current_status_is_selected(self):
        self.client.force_login(self.agent)
        response = self.client.get(self.url)
        self.assertContains(response, 'value="open" selected')
        self.issue.refresh_from_db()
        self.assertTrue(self.issue.issue_open)
        self.assertEqual(self.client.delete(self.url).status_code, 405)

    def test_invalid_fields_do_not_save_any_changes(self):
        self.client.force_login(self.agent)
        for field, value in [('priority', 999999), ('assigned', 999999),
                             ('issue_open', 'invalid'), ('issue_open', '')]:
            payload = dict(self.payload, **{field: value})
            response = self.client.post(self.url, payload)
            self.assertEqual(response.status_code, 200)
            self.assertIn(field, response.context['form'].errors)
            self.assertEqual(response.context['form'].data[field], str(value))
            self.issue.refresh_from_db()
            self.assertTrue(self.issue.issue_open)
            self.assertEqual(self.issue.priority, self.priority)
            self.assertEqual(self.issue.assigned_id, self.other.pk)

    def test_csrf_is_enforced(self):
        from django.test import Client
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.agent)
        self.assertEqual(client.post(self.url, self.payload).status_code, 403)
        client.get(self.url)
        response = client.post(self.url, self.payload,
                               HTTP_X_CSRFTOKEN=client.cookies['csrftoken'].value)
        self.assertEqual(response.status_code, 302)

    def test_missing_ticket_returns_404_for_agent(self):
        self.client.force_login(self.agent)
        url = reverse('issues:issue_edit', args=[999999])
        self.assertEqual(self.client.get(url).status_code, 404)
        self.assertEqual(self.client.post(url, self.payload).status_code, 404)

    def test_controls_follow_permissions_and_dashboard_reflects_changes(self):
        detail = reverse('issues:issue', args=[self.issue.pk])
        self.assertNotContains(self.client.get(detail), 'Update ticket')
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(detail), 'Update ticket')
        self.client.force_login(self.agent)
        self.assertContains(self.client.get(detail), self.url)
        self.client.post(self.url, self.payload)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.context['num_open_issues'], 0)
        self.payload['issue_open'] = 'open'
        self.client.post(self.url, self.payload)
        response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.context['num_open_issues'], 1)
        self.assertEqual(response.context['num_my_issues'], 1)
