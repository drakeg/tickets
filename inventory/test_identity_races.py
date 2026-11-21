"""Database-backed uniqueness for new/renamed systems without legacy rewrites."""
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.utils import timezone

from inventory.forms import InventoryForm, ServerAdminForm
from inventory.models import Cluster, Operating_System, Server, Vendor


class CanonicalAssetIdentityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.os = Operating_System.objects.create(os_name='Ubuntu')
        cls.vendor = Vendor.objects.create(vendor_name='Fixture vendor')
        cls.primary = Cluster.objects.create(cluster_name='Production')
        cls.secondary = Cluster.objects.create(cluster_name='Staging')

    def form(self, name, *, cluster=None, instance=None, admin=False):
        form_class = ServerAdminForm if admin else InventoryForm
        data = {
            'server_name': name, 'cluster': (cluster or self.primary).pk,
            'os': self.os.pk, 'vendor': self.vendor.pk,
        }
        if admin:
            data['pub_date'] = timezone.now().strftime('%Y-%m-%d %H:%M:%S')
        return form_class(data=data, instance=instance)

    def save(self, name, **kwargs):
        form = self.form(name, **kwargs)
        self.assertTrue(form.is_valid(), form.errors)
        server = form.save(commit=False)
        if not server.pub_date:
            server.pub_date = timezone.now()
        server.save()
        return server

    def test_new_system_gets_unique_canonical_key(self):
        first = self.save('  VPN-Gateway  ')
        self.assertEqual(first.server_name, 'VPN-Gateway')
        self.assertEqual(first.identity_key, f'{self.primary.pk}:vpn-gateway')
        other = self.save('vpn-GATEWAY', cluster=self.secondary)
        self.assertEqual(other.identity_key, f'{self.secondary.pk}:vpn-gateway')
        self.assertEqual(Server.objects.count(), 2)

    def test_prevalidated_concurrent_forms_cannot_create_duplicate_key(self):
        first = self.form('Edge-01')
        second = self.form('EDGE-01')
        self.assertTrue(first.is_valid(), first.errors)
        self.assertTrue(second.is_valid(), second.errors)
        item = first.save(commit=False)
        item.pub_date = timezone.now()
        item.save()
        competing = second.save(commit=False)
        competing.pub_date = timezone.now()
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                competing.save()
        self.assertEqual(Server.objects.filter(cluster=self.primary).count(), 1)

    def test_admin_and_regular_forms_share_database_uniqueness(self):
        admin_form = self.form('web-01', admin=True)
        regular_form = self.form('WEB-01')
        self.assertTrue(admin_form.is_valid(), admin_form.errors)
        self.assertTrue(regular_form.is_valid(), regular_form.errors)
        admin_form.save()
        later = regular_form.save(commit=False)
        later.pub_date = timezone.now()
        with transaction.atomic():
            with self.assertRaises(IntegrityError):
                later.save()
        self.assertEqual(Server.objects.count(), 1)

    def test_legacy_null_key_survives_unrelated_admin_edits(self):
        legacy = Server.objects.create(
            server_name='host-01', os=self.os, vendor=self.vendor,
            cluster=self.primary, pub_date=timezone.now(),
        )
        self.assertIsNone(legacy.identity_key)
        form = self.form('host-01', instance=legacy, admin=True)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        legacy.refresh_from_db()
        self.assertIsNone(legacy.identity_key)

    def test_identity_change_from_legacy_row_creates_canonical_key(self):
        legacy = Server.objects.create(
            server_name='old-host', os=self.os, vendor=self.vendor,
            cluster=self.primary, pub_date=timezone.now(),
        )
        form = self.form('new-host', instance=legacy, admin=True)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        legacy.refresh_from_db()
        self.assertEqual(legacy.identity_key, f'{self.primary.pk}:new-host')

    def test_legacy_padded_name_blocks_new_conflicting_identity(self):
        Server.objects.create(
            server_name='  PROD-01 ', os=self.os, vendor=self.vendor,
            cluster=self.primary, pub_date=timezone.now(),
        )
        form = self.form('prod-01')
        self.assertFalse(form.is_valid())
        self.assertIn('server_name', form.errors)
        self.assertEqual(Server.objects.count(), 1)

    def test_unicode_casefold_blocks_equivalent_new_identifiers(self):
        self.save('Straße')
        form = self.form('STRASSE')
        self.assertFalse(form.is_valid())
        self.assertIn('server_name', form.errors)

    def test_historical_same_cluster_duplicates_stay_untouched(self):
        first = Server.objects.create(
            server_name='legacy', os=self.os, vendor=self.vendor,
            cluster=self.primary, pub_date=timezone.now(),
        )
        second = Server.objects.create(
            server_name=' LEGACY ', os=self.os, vendor=self.vendor,
            cluster=self.primary, pub_date=timezone.now(),
        )
        self.assertIsNone(first.identity_key)
        self.assertIsNone(second.identity_key)
        form = self.form('legacy', instance=first, admin=True)
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertEqual(Server.objects.filter(cluster=self.primary).count(), 2)
        self.assertIsNone(Server.objects.get(pk=first.pk).identity_key)
        self.assertIsNone(Server.objects.get(pk=second.pk).identity_key)
