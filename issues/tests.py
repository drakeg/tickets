from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Issue, Priority


def grant_ticket_access(user, *codenames):
    user.user_permissions.add(*Permission.objects.filter(
        content_type__app_label='issues', codename__in=codenames))


class IssueWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="issue-user",
            password="test-password",
        )
        grant_ticket_access(self.user, 'view_issue', 'add_issue', 'view_priority')
        self.client.force_login(self.user)
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
        self.client.logout()
        response = self.client.get(reverse("issues:issue_new"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_my_issues_requires_authentication(self):
        self.client.logout()
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
        self.client.logout()
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

    def setUp(self):
        grant_ticket_access(self.user, 'view_issue')
        self.client.force_login(self.user)

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
        grant_ticket_access(cls.agent, 'view_issue', 'change_issue', 'view_priority')
        cls.other = get_user_model().objects.create_user(username='unprivileged', is_staff=True)
        grant_ticket_access(cls.other, 'view_issue')
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
        self.assertEqual(self.client.get(detail).status_code, 302)
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


class IssueHistoryTests(TestCase):
    setUpTestData = classmethod(IssueTriageTests.setUpTestData.__func__)

    def setUp(self):
        self.client.force_login(self.agent)
        self.url = reverse('issues:issue_edit', args=[self.issue.pk])
        self.detail = reverse('issues:issue', args=[self.issue.pk])
        self.payload = {'issue_open': 'closed', 'priority': self.urgent.pk, 'assigned': ''}

    def test_changed_values_and_actor_are_recorded_once(self):
        response = self.client.post(self.url, self.payload)
        self.assertEqual(response.status_code, 302)
        event = self.issue.changes.get()
        self.assertEqual(event.actor, self.agent)
        self.assertEqual(event.actor_name, 'agent')
        self.assertEqual(event.before['status'], 'Open')
        self.assertEqual(event.after['status'], 'Closed')
        self.assertEqual(event.before['priority'], {'id': self.priority.pk, 'name': 'Normal'})
        self.assertEqual(event.after['priority'], {'id': self.urgent.pk, 'name': 'Urgent'})
        self.assertEqual(event.before['assigned']['id'], self.other.pk)
        self.assertEqual(event.after['assigned'], {'id': None, 'name': 'Unassigned'})
        self.client.post(self.url, self.payload)
        self.assertEqual(self.issue.changes.count(), 1)

    def test_invalid_forbidden_and_get_requests_create_no_history(self):
        self.client.get(self.url)
        self.client.post(self.url, dict(self.payload, priority='999999'))
        self.client.force_login(self.other)
        self.assertEqual(self.client.post(self.url, self.payload).status_code, 403)
        self.assertFalse(self.issue.changes.exists())

    def test_event_failure_rolls_back_ticket_update(self):
        from unittest.mock import patch
        from django.db import IntegrityError
        with patch('issues.services.IssueChange.objects.create', side_effect=IntegrityError('failure')):
            with self.assertRaises(IntegrityError):
                self.client.post(self.url, self.payload)
        self.issue.refresh_from_db()
        self.assertTrue(self.issue.issue_open)
        self.assertEqual(self.issue.priority, self.priority)
        self.assertEqual(self.issue.assigned_id, self.other.pk)
        self.assertFalse(self.issue.changes.exists())

    def test_deleted_or_renamed_users_do_not_rewrite_historical_names(self):
        self.client.post(self.url, self.payload)
        self.agent.username = 'renamed'
        self.agent.save()
        self.agent.delete()
        event = self.issue.changes.get()
        self.assertIsNone(event.actor)
        self.assertEqual(event.actor_name, 'agent')
        self.assertEqual(event.before['assigned']['name'], 'unprivileged')
        self.priority.name = 'Renamed priority'
        self.priority.save()
        event.refresh_from_db()
        self.assertEqual(event.before['priority']['name'], 'Normal')

    def test_history_requires_edit_permission_and_escapes_actor_names(self):
        self.agent.username = '<script>unsafe</script>'
        self.agent.save()
        self.client.post(self.url, self.payload)
        response = self.client.get(self.detail)
        self.assertContains(response, '&lt;script&gt;unsafe&lt;/script&gt;')
        self.assertContains(response, 'Change history')
        self.client.force_login(self.other)
        self.assertNotContains(self.client.get(self.detail), 'Change history')
        self.client.logout()
        self.assertEqual(self.client.get(self.detail).status_code, 302)

    def test_history_pagination_is_stable_and_scoped_to_ticket(self):
        from .models import IssueChange
        from .services import triage_snapshot
        state = triage_snapshot(self.issue)
        events = [IssueChange.objects.create(
            issue=self.issue, actor=self.agent, actor_name='agent', before=state, after=state,
        ) for _ in range(12)]
        timestamp = timezone.now()
        self.issue.changes.update(created_at=timestamp)
        ids = []
        for number in (1, 2):
            response = self.client.get(self.detail, {'history_page': number})
            ids.extend(event.pk for event in response.context['history'])
        self.assertEqual(ids, [event.pk for event in reversed(events)])
        self.assertEqual(self.client.get(self.detail, {'history_page': 'bad'}).status_code, 200)
        other_issue = Issue.objects.create(requestor_name='other', summary='Other',
            description='Other', priority=self.priority, pub_date=timestamp)
        self.assertContains(self.client.get(reverse('issues:issue', args=[other_issue.pk])),
                            'No recorded changes.')


class TicketRoleBoundaryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        from django.contrib.auth.models import Group
        from django.core.management import call_command
        from io import StringIO
        call_command('setup_roles', stdout=StringIO())
        cls.users = {}
        for role in ('Infrastructure Team', 'Help Desk', 'Project Manager'):
            user = get_user_model().objects.create_user(username=role.replace(' ', '-'))
            user.groups.add(Group.objects.get(name=role))
            cls.users[role] = user
        cls.no_role = get_user_model().objects.create_user(username='no-role', is_staff=True)
        cls.priority = Priority.objects.create(name='Normal')
        cls.ticket = Issue.objects.create(requestor_name='private requestor',
            summary='Private ticket marker', description='Private details',
            priority=cls.priority, pub_date=timezone.now(), assigned=cls.no_role)

    def routes(self):
        return [reverse('issues:' + name) for name in
                ('index', 'my_issues', 'unassigned_issues', 'search')] + [
                    reverse('issues:issue', args=[self.ticket.pk])]

    def payload(self):
        return {'summary': 'New request', 'description': 'Details',
                'priority': self.priority.pk, 'issue_open': 'closed', 'assigned': ''}

    def test_anonymous_and_no_role_cannot_read_any_ticket_entry_point(self):
        for url in self.routes():
            self.assertEqual(self.client.get(url, {'q': 'Private'}).status_code, 302)
        self.client.force_login(self.no_role)
        for url in self.routes():
            response = self.client.get(url, {'q': 'Private'})
            self.assertEqual(response.status_code, 403)
            self.assertNotContains(response, self.ticket.summary, status_code=403)
        # Even an assigned staff user has no implicit ticket grant.
        response = self.client.get(reverse('issues:issue', args=[999999]))
        self.assertEqual(response.status_code, 403)

    def test_named_roles_can_read_but_only_granted_roles_can_write(self):
        create = reverse('issues:issue_new')
        edit = reverse('issues:issue_edit', args=[self.ticket.pk])
        for role, user in self.users.items():
            self.client.force_login(user)
            for url in self.routes():
                self.assertEqual(self.client.get(url).status_code, 200)
            self.assertEqual(self.client.get(create).status_code, 200 if role == 'Help Desk' else 403)
            self.assertEqual(self.client.get(edit).status_code, 403 if role == 'Project Manager' else 200)
            before = Issue.objects.count()
            response = self.client.post(create, self.payload())
            self.assertEqual(response.status_code, 302 if role == 'Help Desk' else 403)
            self.assertEqual(Issue.objects.count(), before + (role == 'Help Desk'))
            response = self.client.post(edit, self.payload())
            self.assertEqual(response.status_code, 403 if role == 'Project Manager' else 302)
        self.assertEqual(self.client.get(reverse('admin:index')).status_code, 302)

    def test_denied_posts_do_not_write_ticket_or_history(self):
        self.client.force_login(self.no_role)
        self.assertEqual(self.client.post(reverse('issues:issue_new'), self.payload()).status_code, 403)
        self.assertEqual(self.client.post(reverse('issues:issue_edit', args=[self.ticket.pk]),
                                         self.payload()).status_code, 403)
        self.ticket.refresh_from_db()
        self.assertTrue(self.ticket.issue_open)
        self.assertFalse(self.ticket.changes.exists())
        self.assertEqual(Issue.objects.count(), 1)

    def test_write_and_reference_grants_do_not_replace_ticket_view_permission(self):
        grant_ticket_access(self.no_role, 'add_issue', 'change_issue', 'view_priority')
        self.client.force_login(self.no_role)
        for url in [reverse('issues:issue_new'), reverse('issues:issue_edit', args=[self.ticket.pk])]:
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)
        grant_ticket_access(self.no_role, 'view_issue')
        self.no_role.user_permissions.remove(Permission.objects.get(
            content_type__app_label='issues', codename='view_priority'))
        for url in [reverse('issues:issue_new'), reverse('issues:issue_edit', args=[self.ticket.pk])]:
            self.assertEqual(self.client.get(url).status_code, 403)
            self.assertEqual(self.client.post(url, self.payload()).status_code, 403)
        self.assertNotContains(self.client.get(reverse('issues:issue', args=[self.ticket.pk])), 'Update ticket')

    def test_dashboard_hides_ticket_counts_links_and_queries_without_view_grant(self):
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        self.client.force_login(self.no_role)
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(reverse('dashboard:index'))
        self.assertEqual(response.context['num_open_issues'], 0)
        self.assertEqual(response.context['num_my_issues'], 0)
        self.assertFalse(any('"issues_issue"' in query['sql'] for query in queries))
        for url in self.routes() + [reverse('issues:issue_new')]:
            self.assertNotContains(response, 'href="' + url)
        self.client.force_login(self.users['Project Manager'])
        response = self.client.get(reverse('dashboard:index'))
        self.assertContains(response, 'href="' + reverse('issues:index'))
        self.assertNotContains(response, 'href="' + reverse('issues:issue_new'))
        self.assertEqual(response.context['num_open_issues'], 1)
        self.client.force_login(self.users['Help Desk'])
        self.assertContains(self.client.get(reverse('dashboard:index')),
                            'href="' + reverse('issues:issue_new'))

    def test_revocation_and_combined_roles_apply_on_next_request(self):
        from django.contrib.auth.models import Group
        user = self.users['Project Manager']
        self.client.force_login(user)
        create = reverse('issues:issue_new')
        self.assertEqual(self.client.get(create).status_code, 403)
        user.groups.add(Group.objects.get(name='Help Desk'))
        self.assertEqual(self.client.get(create).status_code, 200)
        user.groups.remove(Group.objects.get(name='Help Desk'))
        self.assertEqual(self.client.get(create).status_code, 403)
        self.assertEqual(self.client.get(self.routes()[0]).status_code, 200)
        user.groups.clear()
        self.assertEqual(self.client.get(self.routes()[0]).status_code, 403)
        self.assertNotContains(self.client.get(reverse('dashboard:index')),
                               'href="' + reverse('issues:index'))

    def test_superuser_can_recover_without_group_membership(self):
        user = get_user_model().objects.create_superuser(username='recovery', password='test-only')
        self.client.force_login(user)
        self.assertEqual(self.client.get(self.routes()[0]).status_code, 200)
        self.assertEqual(self.client.get(reverse('issues:issue_new')).status_code, 200)
        self.assertEqual(self.client.get(reverse('issues:issue_edit', args=[self.ticket.pk])).status_code, 200)



class IssueAdminAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin_user = get_user_model().objects.create_superuser(
            username='audit-admin', password='test-password',
        )
        cls.assignee = get_user_model().objects.create_user(username='assignee')
        cls.normal = Priority.objects.create(name='Normal')
        cls.urgent = Priority.objects.create(name='Urgent')
        cls.issue = Issue.objects.create(
            requestor_name='requestor', summary='Original', description='Original',
            priority=cls.normal, pub_date=timezone.now(), assigned=cls.assignee,
        )

    def setUp(self):
        from django.contrib import admin
        from django.test import RequestFactory
        self.issue_admin = admin.site._registry[Issue]
        self.request = RequestFactory().post('/admin/issues/issue/')
        self.request.user = self.admin_user

    def test_admin_triage_change_records_snapshot_and_actor(self):
        changed = Issue.objects.get(pk=self.issue.pk)
        changed.issue_open = False
        changed.priority = self.urgent
        changed.assigned = None
        self.issue_admin.save_model(self.request, changed, None, change=True)
        event = self.issue.changes.get()
        self.assertEqual(event.actor, self.admin_user)
        self.assertEqual(event.actor_name, 'audit-admin')
        self.assertEqual(event.before['status'], 'Open')
        self.assertEqual(event.after['status'], 'Closed')
        self.assertEqual(event.before['priority']['name'], 'Normal')
        self.assertEqual(event.after['priority']['name'], 'Urgent')
        self.assertEqual(event.after['assigned']['id'], None)

    def test_content_only_and_noop_edits_do_not_create_triage_history(self):
        changed = Issue.objects.get(pk=self.issue.pk)
        changed.summary = 'Edited by admin'
        self.issue_admin.save_model(self.request, changed, None, change=True)
        self.issue_admin.save_model(self.request, changed, None, change=True)
        self.assertEqual(self.issue.changes.count(), 0)
        self.issue.refresh_from_db()
        self.assertEqual(self.issue.summary, 'Edited by admin')

    def test_admin_create_does_not_record_a_preexisting_state(self):
        created = Issue(
            requestor_name='requestor', summary='New', description='New',
            priority=self.normal, pub_date=timezone.now(),
        )
        self.issue_admin.save_model(self.request, created, None, change=False)
        self.assertIsNotNone(created.pk)
        self.assertFalse(created.changes.exists())

    def test_event_failure_rolls_back_admin_ticket_update(self):
        from unittest.mock import patch
        from django.db import IntegrityError
        changed = Issue.objects.get(pk=self.issue.pk)
        changed.issue_open = False
        with patch('issues.admin.IssueChange.objects.create',
                   side_effect=IntegrityError('audit failure')):
            with self.assertRaises(IntegrityError):
                self.issue_admin.save_model(self.request, changed, None, change=True)
        self.issue.refresh_from_db()
        self.assertTrue(self.issue.issue_open)
        self.assertFalse(self.issue.changes.exists())

    def test_nonstaff_cannot_access_admin_change_form(self):
        self.client.force_login(self.assignee)
        response = self.client.get(reverse('admin:issues_issue_change', args=[self.issue.pk]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(self.issue.changes.exists())
