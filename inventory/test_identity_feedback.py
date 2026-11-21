"""Concurrent unique-key error handling for web and Django admin."""
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from inventory.models import Cluster, Operating_System, Server, Vendor
from inventory.tests import grant_inventory_access


IDENTITY_ERROR = IntegrityError(
    'UNIQUE constraint failed: inventory_server.identity_key'
)


class SystemIdentityConflictResponseTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.os = Operating_System.objects.create(os_name='Fixture OS')
        cls.vendor = Vendor.objects.create(vendor_name='Fixture vendor')
        cls.cluster = Cluster.objects.create(cluster_name='Fixture cluster')
        cls.operator = get_user_model().objects.create_user(username='conflict-operator')
        grant_inventory_access(cls.operator)
        cls.admin = get_user_model().objects.create_superuser(
            username='conflict-admin', password='test-pass',
        )

    def payload(self, *, admin=False):
        data = {
            'server_name': 'vpn-gateway',
            'os': self.os.pk,
            'vendor': self.vendor.pk,
            'cluster': self.cluster.pk,
        }
        if admin:
            data['pub_date_0'] = '2026-11-21'
            data['pub_date_1'] = '10:00:00'
            data['_save'] = 'Save'
        return data

    def test_web_race_shows_inline_conflict_without_creating_asset(self):
        self.client.force_login(self.operator)
        with patch('inventory.views.Server.save', side_effect=IDENTITY_ERROR):
            response = self.client.post(
                reverse('inventory:servers_new'), self.payload(),
            )
        self.assertEqual(response.status_code, 200)
        self.assertIn('server_name', response.context['form'].errors)
        self.assertContains(response, 'Another operator saved a system')
        self.assertEqual(Server.objects.count(), 0)

    def test_unrelated_integrity_errors_are_not_swallowed(self):
        self.client.force_login(self.operator)
        other_error = IntegrityError('FOREIGN KEY constraint failed')
        with patch('inventory.views.Server.save', side_effect=other_error):
            with self.assertRaises(IntegrityError):
                self.client.post(reverse('inventory:servers_new'), self.payload())

    def test_admin_race_redirects_to_form_with_error_message(self):
        self.client.force_login(self.admin)
        url = reverse('admin:inventory_server_add')
        with patch(
            'inventory.admin.ServerAdmin.save_model', side_effect=IDENTITY_ERROR,
        ):
            response = self.client.post(url, self.payload(admin=True))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], url)
        self.assertEqual(Server.objects.count(), 0)
        from django.contrib.messages import get_messages
        messages = [str(message) for message in get_messages(response.wsgi_request)]
        self.assertTrue(any('Another operator saved' in message for message in messages))

    def test_unrelated_admin_integrity_error_is_not_swallowed(self):
        self.client.force_login(self.admin)
        with patch(
            'inventory.admin.ServerAdmin.save_model',
            side_effect=IntegrityError('FOREIGN KEY constraint failed'),
        ):
            with self.assertRaises(IntegrityError):
                self.client.post(
                    reverse('admin:inventory_server_add'), self.payload(admin=True),
                )
