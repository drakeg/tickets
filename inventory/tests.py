from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Cluster, Operating_System, Server, Vendor


class InventoryWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="inventory-user",
            password="test-password",
        )
        self.staff_user = get_user_model().objects.create_user(
            username="inventory-admin",
            password="test-password",
            is_staff=True,
        )
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

    def test_server_create_requires_authentication(self):
        response = self.client.get(reverse("inventory:servers_new"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_server_form_creates_server(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("inventory:servers_new"),
            {
                "server_name": "app-02",
                "os": self.os.pk,
                "vendor": self.vendor.pk,
                "cluster": self.cluster.pk,
            },
        )

        created = Server.objects.get(server_name="app-02")
        self.assertEqual(created.cluster, self.cluster)
        self.assertRedirects(response, reverse('inventory:servers', args=[created.pk]))
        self.client.get(response['Location'])
        self.assertEqual(Server.objects.filter(server_name='app-02').count(), 1)

    def test_vendor_create_requires_authentication(self):
        response = self.client.get(reverse("inventory:vendor_new"))

        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("login"), response["Location"])

    def test_vendor_create_rejects_non_staff_user(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("inventory:vendor_new"))

        self.assertEqual(response.status_code, 403)

    def test_staff_user_can_create_vendor(self):
        self.client.force_login(self.staff_user)

        response = self.client.post(
            reverse("inventory:vendor_new"),
            {"vendor_name": "Lenovo"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(Vendor.objects.filter(vendor_name="Lenovo").exists())


    def test_system_detail_displays_relationships(self):
        response = self.client.get(reverse('inventory:servers', args=[self.server.pk]))
        for value in ('app-01', 'Ubuntu', 'Dell', 'Production', 'Created'):
            self.assertContains(response, value)
        self.assertContains(response, reverse('inventory:index'))

    def test_invalid_reference_retains_input_and_does_not_create_system(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse('inventory:servers_new'), {
            'server_name': 'Keep this name', 'os': 999999,
            'vendor': self.vendor.pk, 'cluster': self.cluster.pk,
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('os', response.context['form'].errors)
        self.assertContains(response, 'Keep this name')
        self.assertEqual(Server.objects.count(), 1)

    def test_anonymous_post_cannot_create_system(self):
        response = self.client.post(reverse('inventory:servers_new'), {
            'server_name': 'Blocked', 'os': self.os.pk,
            'vendor': self.vendor.pk, 'cluster': self.cluster.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse('login'), response['Location'])
        self.assertEqual(Server.objects.count(), 1)

    def test_missing_system_returns_404(self):
        response = self.client.get(reverse('inventory:servers', args=[self.server.pk + 1]))
        self.assertEqual(response.status_code, 404)

    def test_system_name_is_escaped(self):
        self.server.server_name = '<script>unsafe</script>'
        self.server.save()
        response = self.client.get(reverse('inventory:servers', args=[self.server.pk]))
        self.assertContains(response, '&lt;script&gt;unsafe&lt;/script&gt;')
        self.assertNotContains(response, '<script>unsafe</script>')


class InventorySetupGuidanceTests(TestCase):
    def test_empty_reference_lists_explain_setup_without_exposing_admin_links(self):
        user = get_user_model().objects.create_user(username='new-operator')
        self.client.force_login(user)
        response = self.client.get(reverse('inventory:servers_new'))
        self.assertContains(response, 'operating systems, vendors, clusters')
        self.assertNotContains(response, reverse('admin:inventory_cluster_add'))
        self.assertEqual(Server.objects.count(), 0)

    def test_administrator_can_reach_setup_and_notice_clears_when_ready(self):
        admin = get_user_model().objects.create_superuser(username='setup-admin', password='test-password')
        self.client.force_login(admin)
        response = self.client.get(reverse('inventory:servers_new'))
        for route in ('admin:inventory_operating_system_add', 'admin:inventory_vendor_add',
                      'admin:inventory_cluster_add'):
            self.assertContains(response, reverse(route))
            self.assertEqual(self.client.get(reverse(route)).status_code, 200)
        Operating_System.objects.create(os_name='Ubuntu')
        Vendor.objects.create(vendor_name='Dell')
        Cluster.objects.create(cluster_name='Production')
        response = self.client.get(reverse('inventory:servers_new'))
        self.assertNotContains(response, 'Before adding a system')
