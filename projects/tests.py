import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Project


class ProjectWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="project-user",
            password="test-password",
        )
        self.project = Project.objects.create(
            requestor_name="project-user",
            summary="Upgrade servers",
            description="Upgrade application servers",
            pub_date=timezone.now(),
            start_date=datetime.date.today(),
            end_date=datetime.date.today() + datetime.timedelta(days=30),
            assigned=self.user,
        )

    def test_project_detail_returns_requested_project(self):
        response = self.client.get(
            reverse("projects:project", args=[self.project.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["project"], self.project)

    def test_project_search_matches_project_fields(self):
        response = self.client.get(
            reverse("projects:search"),
            {"q": "servers"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["project_list"],
            [self.project],
            transform=lambda project: project,
        )

    def test_empty_project_search_returns_empty_result(self):
        response = self.client.get(reverse("projects:search"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["project_list"]), [])

    def test_project_create_requires_authentication(self):
        response = self.client.get(reverse("projects:project_new"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_my_projects_requires_authentication(self):
        response = self.client.get(reverse("projects:my_projects"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_my_projects_only_returns_assignments_for_current_user(self):
        other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )
        Project.objects.create(
            requestor_name="other-user",
            summary="Other project",
            description="Not assigned to current user",
            pub_date=timezone.now(),
            assigned=other_user,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("projects:my_projects"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["project_list"]), [self.project])

    def test_authenticated_user_can_create_project(self):
        self.client.force_login(self.user)
        today = datetime.date.today()

        response = self.client.post(
            reverse("projects:project_new"),
            {
                "summary": "New project",
                "description": "Created through the project form",
                "start_date": today.isoformat(),
                "end_date": (today + datetime.timedelta(days=14)).isoformat(),
                "assigned": self.user.pk,
            },
        )

        created = Project.objects.get(summary="New project")
        self.assertEqual(created.requestor_name, self.user.username)
        self.assertEqual(created.assigned, self.user)

        self.assertRedirects(response, reverse('projects:project', args=[created.pk]))
        self.client.get(response['Location'])
        self.assertEqual(Project.objects.filter(summary='New project').count(), 1)

    def test_invalid_project_retains_values_and_does_not_save(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('projects:project_new'), {
            'summary': '', 'description': 'Retain this description', 'start_date': 'not-a-date',
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('summary', response.context['form'].errors)
        self.assertIn('start_date', response.context['form'].errors)
        self.assertContains(response, 'Retain this description')
        self.assertEqual(Project.objects.count(), 1)

    def test_project_detail_displays_content_assignment_and_dates(self):
        response = self.client.get(reverse('projects:project', args=[self.project.pk]))
        for value in ('Upgrade servers', 'Upgrade application servers', 'project-user',
                      'Start date', 'End date', 'Created'):
            self.assertContains(response, value)
        self.assertContains(response, reverse('projects:index'))

    def test_unassigned_unscheduled_project_escapes_description(self):
        self.project.assigned = None
        self.project.start_date = None
        self.project.end_date = None
        self.project.description = '<script>unsafe</script>\nSecond line'
        self.project.save()
        response = self.client.get(reverse('projects:project', args=[self.project.pk]))
        self.assertContains(response, 'Unassigned')
        self.assertContains(response, 'Not scheduled', count=2)
        self.assertContains(response, '&lt;script&gt;unsafe&lt;/script&gt;')
        self.assertNotContains(response, '<script>unsafe</script>')
        self.assertContains(response, '<br>Second line')

    def test_missing_project_returns_404(self):
        response = self.client.get(reverse('projects:project', args=[self.project.pk + 1]))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_project_post_cannot_create_record(self):
        response = self.client.post(reverse('projects:project_new'), {
            'summary': 'Blocked', 'description': 'Blocked',
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])
        self.assertEqual(Project.objects.count(), 1)


class ProjectSchedulingTests(TestCase):
    def setUp(self):
        user = get_user_model().objects.create_user(username='scheduler')
        self.client.force_login(user)
        self.url = reverse('projects:project_new')
        self.payload = {'summary': 'Scheduled project', 'description': 'Keep this description'}

    def test_reversed_schedule_is_rejected_without_losing_input(self):
        response = self.client.post(self.url, dict(self.payload,
            start_date='2026-12-10', end_date='2026-12-09'))
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'end_date',
                             'End date must be on or after the start date.')
        self.assertContains(response, 'Keep this description')
        self.assertContains(response, 'value="2026-12-10"')
        self.assertContains(response, 'value="2026-12-09"')
        self.assertFalse(Project.objects.exists())

    def test_same_day_and_forward_schedules_are_saved(self):
        for end in ('2026-12-10', '2026-12-11'):
            response = self.client.post(self.url, dict(self.payload,
                start_date='2026-12-10', end_date=end))
            created = Project.objects.latest('pk')
            self.assertRedirects(response, reverse('projects:project', args=[created.pk]))
            self.assertEqual(created.start_date, datetime.date(2026, 12, 10))
            self.assertEqual(created.end_date, datetime.date.fromisoformat(end))

    def test_optional_and_partial_schedules_remain_supported(self):
        for start, end in (('', ''), ('2026-12-10', ''), ('', '2026-12-11')):
            response = self.client.post(self.url, dict(self.payload, start_date=start, end_date=end))
            created = Project.objects.latest('pk')
            self.assertRedirects(response, reverse('projects:project', args=[created.pk]))
            self.assertEqual(created.start_date, datetime.date.fromisoformat(start) if start else None)
            self.assertEqual(created.end_date, datetime.date.fromisoformat(end) if end else None)

    def test_date_controls_are_native_and_invalid_date_is_rejected(self):
        from html.parser import HTMLParser
        class InputParser(HTMLParser):
            inputs = None
            def handle_starttag(self, tag, attrs):
                if tag == 'input':
                    values = dict(attrs)
                    self.inputs[values.get('name')] = values
        response = self.client.get(self.url)
        parser = InputParser()
        parser.inputs = {}
        parser.feed(response.content.decode())
        for field in ('start_date', 'end_date'):
            self.assertEqual(parser.inputs[field]['type'], 'date')
        response = self.client.post(self.url, dict(self.payload,
            start_date='2026-02-30', end_date='2026-12-10'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('start_date', response.context['form'].errors)
        self.assertFalse(Project.objects.exists())


class ProjectListTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create_user(username='project-reader')
        cls.other = get_user_model().objects.create_user(username='other-reader')
        now = timezone.now()
        cls.projects = [Project.objects.create(
            requestor_name='Requestor', summary=f'Network {number}',
            description='Network & access', pub_date=now,
            assigned=cls.user if number % 2 else None,
        ) for number in range(34)]
        cls.foreign = Project.objects.create(
            requestor_name='Other', summary='Unrelated', description='Different work',
            pub_date=now, assigned=cls.other,
        )

    def test_all_projects_are_reachable_with_stable_ordering(self):
        ids = []
        for number in (1, 2, 3):
            response = self.client.get(reverse('projects:index'), {'page': number})
            self.assertEqual(response.status_code, 200)
            ids.extend(project.pk for project in response.context['project_list'])
        self.assertEqual(ids, list(Project.objects.order_by('-pub_date', '-pk').values_list('pk', flat=True)))
        self.assertEqual(len(ids), len(set(ids)))

    def test_assignment_scopes_persist_across_pages(self):
        self.client.force_login(self.user)
        for route, filters in [('my_projects', {'assigned': self.user}),
                               ('unassigned_projects', {'assigned__isnull': True})]:
            ids = []
            for number in (1, 2):
                response = self.client.get(reverse('projects:' + route), {'page': number})
                ids.extend(project.pk for project in response.context['project_list'])
            self.assertEqual(ids, list(Project.objects.filter(**filters).order_by(
                '-pub_date', '-pk').values_list('pk', flat=True)))
            self.assertNotIn(self.foreign.pk, ids)

    def test_search_paging_preserves_encoded_query_and_matching_scope(self):
        ids = []
        for number in (1, 2, 3):
            response = self.client.get(reverse('projects:search'), {
                'q': ' Network & access ', 'page': number,
            })
            self.assertContains(response, 'q=Network%20%26%20access')
            self.assertEqual(response.context['query'], 'Network & access')
            ids.extend(project.pk for project in response.context['project_list'])
        self.assertEqual(ids, [project.pk for project in reversed(self.projects)])

    def test_empty_results_and_invalid_pages_are_safe(self):
        for value, expected in [('invalid', 1), ('999', 3), ('0', 3)]:
            response = self.client.get(reverse('projects:index'), {'page': value})
            self.assertEqual(response.context['page_obj'].number, expected)
        for query in ('', '   ', 'no match'):
            response = self.client.get(reverse('projects:search'), {'q': query, 'page': 99})
            self.assertContains(response, 'No projects are available.')
            self.assertNotContains(response, 'aria-label="Project pages"')

    def test_list_shows_real_schedule_instead_of_inert_status_control(self):
        response = self.client.get(reverse('projects:index'))
        self.assertContains(response, 'Not scheduled')
        self.assertContains(response, 'Unassigned')
        self.assertContains(response, self.foreign.summary)
        self.assertContains(response, reverse('projects:project_new'))
        self.assertNotContains(response, 'Closed/Opened')
        self.assertNotContains(response, 'type="checkbox"')
