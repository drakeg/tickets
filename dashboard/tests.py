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
