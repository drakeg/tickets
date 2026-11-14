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
        self.assertContains(response, 'aria-label="Main navigation"')
        self.assertNotContains(response, 'data-bs-toggle="dropdown"')
        self.assertContains(response, '/static/tickets/vendor/bootstrap-5.3.3.min.css')


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

    def test_dashboard_links_my_ticket_count_to_personal_queue(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.context["max_my_issues"], 100)
        self.assertContains(response, reverse("issues:my_issues"))


class DashboardAuthorizationNavigationTests(TestCase):
    def test_anonymous_navigation_explains_authentication_for_create_actions(self):
        response = self.client.get(reverse("dashboard:index"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'sign in')
        self.assertNotContains(response, reverse('inventory:vendor_new'))
        self.assertNotContains(response, reverse('admin:index'))

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
        self.assertNotIn('https://cdn', content)
        self.assertNotIn('data-bs-toggle', content)
        self.assertIn('/static/tickets/vendor/bootstrap-5.3.3.min.css', content)


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

        from html.parser import HTMLParser
        class IdParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.ids = []
            def handle_starttag(self, tag, attrs):
                self.ids.extend(value for key, value in attrs if key == 'id')
        parser = IdParser()
        parser.feed(content)
        self.assertEqual(len(parser.ids), len(set(parser.ids)))
        self.assertNotIn('collapse navbar-collapse', content)


class WorkspaceNavigationTests(TestCase):
    def test_signed_out_create_links_lead_to_login(self):
        response = self.client.get(reverse('dashboard:index'))
        self.assertContains(response, 'sign in')
        for route in ('issues:issue_new', 'projects:project_new',
                      'inventory:servers_new', 'knowledgebase:new'):
            path = reverse(route)
            self.assertContains(response, 'href="' + path + '"')
            result = self.client.get(path)
            self.assertEqual(result.status_code, 302)
            self.assertIn(reverse('login'), result['Location'])

    def test_signed_in_create_links_open_forms_and_navigation_has_no_dead_links(self):
        user = get_user_model().objects.create_user(username='navigation-user')
        self.client.force_login(user)
        response = self.client.get(reverse('dashboard:index'))
        self.assertNotContains(response, 'href="#"')
        for route in ('issues:issue_new', 'projects:project_new',
                      'inventory:servers_new', 'knowledgebase:new'):
            self.assertEqual(self.client.get(reverse(route)).status_code, 200)
        self.assertContains(response, reverse('projects:index'))
        self.assertNotContains(response, reverse('admin:index'))
        user.is_staff = True
        user.save()
        self.assertContains(self.client.get(reverse('dashboard:index')), reverse('admin:index'))


class WorkspaceContrastTests(TestCase):
    def test_muted_text_and_outline_buttons_meet_normal_text_contrast(self):
        import re
        from pathlib import Path
        from django.conf import settings

        css = (Path(settings.BASE_DIR) / 'static/tickets/css/tickets.css').read_text()
        muted = re.search(r'--muted:\s*(#[0-9a-fA-F]{6})', css).group(1)

        def luminance(value):
            channels = [int(value[i:i + 2], 16) / 255 for i in (1, 3, 5)]
            linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
                      for c in channels]
            return sum(c * weight for c, weight in zip(linear, (0.2126, 0.7152, 0.0722)))

        for foreground, background in (
            (muted, '#f3f6fa'), (muted, '#ffffff'), ('#ffffff', muted),
            ('#08746f', '#f3f6fa'), ('#ffffff', '#08746f'),
        ):
            with self.subTest(foreground=foreground, background=background):
                light, dark = sorted((luminance(foreground), luminance(background)), reverse=True)
                self.assertGreaterEqual((light + 0.05) / (dark + 0.05), 4.5)
