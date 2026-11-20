from django.contrib import admin
from django.test import TestCase
from django.utils import timezone

from inventory.forms import ServerAdminForm
from inventory.models import Cluster, Operating_System, Server, Vendor


class AdminSystemNameValidationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.os = Operating_System.objects.create(os_name='Ubuntu')
        cls.vendor = Vendor.objects.create(vendor_name='Original vendor')
        cls.other_vendor = Vendor.objects.create(vendor_name='Other vendor')
        cls.production = Cluster.objects.create(cluster_name='Production')
        cls.staging = Cluster.objects.create(cluster_name='Staging')
        cls.existing = Server.objects.create(
            server_name='VPN-Gateway', os=cls.os, vendor=cls.vendor,
            cluster=cls.production, pub_date=timezone.now(),
        )

    def form(self, name, *, cluster=None, instance=None, vendor=None):
        return ServerAdminForm(
            data={
                'server_name': name, 'os': self.os.pk,
                'vendor': vendor or self.vendor.pk,
                'cluster': cluster or self.production.pk,
                'pub_date': timezone.now().strftime('%Y-%m-%d %H:%M:%S'),
            },
            instance=instance,
        )

    def test_admin_registration_uses_protected_form(self):
        self.assertIs(admin.site._registry[Server].form, ServerAdminForm)

    def test_admin_rejects_duplicate_case_and_outer_whitespace(self):
        for name in ('vpn-gateway', ' VPN-GATEWAY '):
            form = self.form(name)
            self.assertFalse(form.is_valid())
            self.assertIn('server_name', form.errors)
        self.assertEqual(Server.objects.count(), 1)

    def test_admin_rejects_blank_new_names(self):
        self.assertFalse(self.form('   ').is_valid())
        self.assertEqual(Server.objects.count(), 1)

    def test_admin_allows_same_name_in_different_cluster(self):
        form = self.form('VPN-Gateway', cluster=self.staging.pk)
        self.assertTrue(form.is_valid(), form.errors)
        saved = form.save()
        self.assertEqual(saved.cluster, self.staging)
        self.assertEqual(saved.server_name, 'VPN-Gateway')
        self.assertIsNotNone(saved.pub_date)

    def test_admin_legacy_duplicate_can_edit_unrelated_fields(self):
        duplicate = Server.objects.create(
            server_name='vpn-gateway', os=self.os, vendor=self.vendor,
            cluster=self.production, pub_date=timezone.now(),
        )
        form = self.form(
            duplicate.server_name, instance=duplicate,
            vendor=self.other_vendor.pk,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        duplicate.refresh_from_db()
        self.assertEqual(duplicate.vendor, self.other_vendor)
        self.assertEqual(Server.objects.filter(cluster=self.production).count(), 2)

    def test_admin_legacy_blank_can_edit_unrelated_fields(self):
        blank = Server.objects.create(
            server_name='   ', os=self.os, vendor=self.vendor,
            cluster=self.production, pub_date=timezone.now(),
        )
        form = self.form('', instance=blank, vendor=self.other_vendor.pk)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        blank.refresh_from_db()
        self.assertEqual(blank.server_name, '   ')
        self.assertEqual(blank.vendor, self.other_vendor)

    def test_admin_cannot_introduce_new_conflict_on_edit(self):
        other = Server.objects.create(
            server_name='web-01', os=self.os, vendor=self.vendor,
            cluster=self.production, pub_date=timezone.now(),
        )
        form = self.form(' VPN-GATEWAY ', instance=other)
        self.assertFalse(form.is_valid())
        self.assertIn('server_name', form.errors)
        other.refresh_from_db()
        self.assertEqual(other.server_name, 'web-01')
