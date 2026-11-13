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
