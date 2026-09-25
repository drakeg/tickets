import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inventory.models import Cluster, Operating_System, Server, Vendor
from issues.models import Issue, Priority
from projects.models import Project


class DashboardTemplateTests(TestCase):
    def test_dashboard_renders_shared_layout(self):
        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ServDesk")
        self.assertContains(response, 'data-bs-toggle="dropdown"')


class DashboardMetricTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="dashboard-user",
            password="test-password",
        )
        self.other_user = get_user_model().objects.create_user(
            username="other-user",
            password="test-password",
        )
        self.priority = Priority.objects.create(name="Normal")

        Issue.objects.create(
            requestor_name="dashboard-user",
            summary="My open issue",
            description="Assigned open issue",
            priority=self.priority,
            pub_date=timezone.now(),
            assigned=self.user,
            issue_open=True,
        )
        Issue.objects.create(
            requestor_name="other-user",
            summary="Other open issue",
            description="Another open issue",
            priority=self.priority,
            pub_date=timezone.now(),
            assigned=self.other_user,
            issue_open=True,
        )
        Issue.objects.create(
            requestor_name="dashboard-user",
            summary="Closed issue",
            description="Should not count as open",
            priority=self.priority,
            pub_date=timezone.now(),
            assigned=self.user,
            issue_open=False,
        )

        today = datetime.date.today()
        Project.objects.create(
            requestor_name="dashboard-user",
            summary="Active project",
            description="Still active",
            pub_date=timezone.now(),
            start_date=today,
            end_date=today + datetime.timedelta(days=7),
        )
        Project.objects.create(
            requestor_name="dashboard-user",
            summary="Past project",
            description="Already ended",
            pub_date=timezone.now(),
            start_date=today - datetime.timedelta(days=14),
            end_date=today - datetime.timedelta(days=1),
        )

        os = Operating_System.objects.create(os_name="Ubuntu")
        vendor = Vendor.objects.create(vendor_name="Dell")
        cluster = Cluster.objects.create(cluster_name="Production")
        Server.objects.create(
            server_name="app-01",
            os=os,
            vendor=vendor,
            cluster=cluster,
            pub_date=timezone.now(),
        )
        Server.objects.create(
            server_name="app-02",
            os=os,
            vendor=vendor,
            cluster=cluster,
            pub_date=timezone.now(),
        )

    def test_dashboard_counts_core_metrics(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["num_systems"], 2)
        self.assertEqual(response.context["num_open_issues"], 2)
        self.assertEqual(response.context["num_my_issues"], 1)
        self.assertEqual(response.context["num_open_projects"], 1)

    def test_dashboard_uses_defined_my_issue_progress_maximum(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.context["max_my_issues"], 100)
        self.assertContains(response, 'aria-valuemax="100"')


class DashboardAuthorizationNavigationTests(TestCase):
    def test_anonymous_navigation_hides_protected_actions(self):
        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, reverse("inventory:servers_new"))
        self.assertNotContains(response, reverse("issues:issue_new"))
        self.assertNotContains(response, reverse("issues:my_issues"))
        self.assertNotContains(response, reverse("projects:project_new"))
        self.assertNotContains(response, reverse("projects:my_projects"))

    def test_authenticated_navigation_shows_protected_actions(self):
        user = get_user_model().objects.create_user(
            username="nav-user",
            password="test-password",
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, reverse("inventory:servers_new"))
        self.assertContains(response, reverse("issues:issue_new"))
        self.assertContains(response, reverse("issues:my_issues"))
        self.assertContains(response, reverse("projects:project_new"))
        self.assertContains(response, reverse("projects:my_projects"))


class FrontendAssetRegressionTests(TestCase):
    def test_shared_layout_omits_unused_legacy_assets(self):
        response = self.client.get(reverse("dashboard:index"))
        content = response.content.decode()

        self.assertNotIn("bootstrap-switch", content)
        self.assertNotIn("jquery.datetimepicker", content)
        self.assertNotIn("popper.js/1.16.1", content)
        self.assertIn("jquery-ui.min.js", content)
        self.assertIn("bootstrap.bundle.min.js", content)


class NavbarMarkupRegressionTests(TestCase):
    def test_shared_navbar_uses_unique_dropdown_ids(self):
        user = get_user_model().objects.create_user(
            username="navbar-user",
            password="test-password",
            is_staff=True,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("dashboard:index"))
        content = response.content.decode()

        dropdown_ids = [
            "systemsDropdown",
            "issuesDropdown",
            "projectsDropdown",
            "knowledgebaseDropdown",
            "adminDropdown",
            "accountDropdown",
        ]
        for dropdown_id in dropdown_ids:
            self.assertEqual(content.count(f'id="{dropdown_id}"'), 1)
            self.assertIn(f'aria-labelledby="{dropdown_id}"', content)

        self.assertNotIn('id="navbarDropdown"', content)
        self.assertNotIn("navbar-fixed-top", content)
        self.assertIn("Knowledge Base", content)
