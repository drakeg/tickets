from django.test import TestCase
from django.urls import reverse


class DashboardTemplateTests(TestCase):
    def test_dashboard_renders_shared_layout(self):
        response = self.client.get(reverse("dashboard:index"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ServDesk")
        self.assertContains(response, 'data-bs-toggle="dropdown"')
