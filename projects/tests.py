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

        self.assertEqual(response.status_code, 200)
        created = Project.objects.get(summary="New project")
        self.assertEqual(created.requestor_name, self.user.username)
        self.assertEqual(created.assigned, self.user)
