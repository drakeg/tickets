from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Cluster, Operating_System, Server, Vendor


class InventoryWorkflowTests(TestCase):
    def setUp(self):
        self.os = Operating_System.objects.create(os_name="Ubuntu")
        self.vendor = Vendor.objects.create(vendor_name="Dell")
        self.cluster = Cluster.objects.create(cluster_name="Production")
        self.server = Server.objects.create(
            server_name="app-01",
            os=self.os,
            vendor=self.vendor,
            cluster=self.cluster,
            pub_date=timezone.now(),
        )

    def test_server_detail_returns_requested_server(self):
        response = self.client.get(
            reverse("inventory:servers", args=[self.server.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["server"], self.server)

    def test_server_search_returns_matching_server(self):
        response = self.client.get(
            reverse("inventory:search"),
            {"q": "app-01"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(
            response.context["server_list"],
            [self.server],
            transform=lambda server: server,
        )

    def test_empty_server_search_returns_empty_result(self):
        response = self.client.get(reverse("inventory:search"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(list(response.context["server_list"]), [])

    def test_operating_system_route_is_callable(self):
        response = self.client.get(
            reverse("inventory:operating_systems", args=[self.os.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, str(self.os.pk))

    def test_server_form_creates_server(self):
        response = self.client.post(
            reverse("inventory:servers_new"),
            {
                "server_name": "app-02",
                "os": self.os.pk,
                "vendor": self.vendor.pk,
                "cluster": self.cluster.pk,
            },
        )

        self.assertEqual(response.status_code, 200)
        created = Server.objects.get(server_name="app-02")
        self.assertEqual(created.cluster, self.cluster)
