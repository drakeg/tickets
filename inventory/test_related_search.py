"""User-facing searches include system, vendor, cluster and operating system."""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from inventory.models import Cluster, Operating_System, Server, Vendor
from inventory.tests import grant_inventory_access


class RelatedAssetSearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.operator = get_user_model().objects.create_user(username='related-search-user')
        grant_inventory_access(cls.operator)
        cls.other = get_user_model().objects.create_user(username='unprivileged-search-user')
        production = Cluster.objects.create(cluster_name='Production')
        staging = Cluster.objects.create(cluster_name='Staging')
        dell = Vendor.objects.create(vendor_name='Dell')
        lenovo = Vendor.objects.create(vendor_name='Lenovo')
        ubuntu = Operating_System.objects.create(os_name='Ubuntu Linux')
        windows = Operating_System.objects.create(os_name='Windows Server')
        cls.first = Server.objects.create(
            server_name='vpn-gateway', cluster=production, os=ubuntu,
            vendor=dell, pub_date=timezone.now(),
        )
        cls.second = Server.objects.create(
            server_name='finance-db', cluster=staging, os=windows,
            vendor=lenovo, pub_date=timezone.now(),
        )
        cls.third = Server.objects.create(
            server_name='production-proxy', cluster=production, os=windows,
            vendor=lenovo, pub_date=timezone.now(),
        )

    def setUp(self):
        self.client.force_login(self.operator)

    def matches(self, query):
        response = self.client.get(reverse('inventory:search'), {'q': query})
        self.assertEqual(response.status_code, 200)
        return [asset.pk for asset in response.context['server_list']], response

    def test_search_matches_system_name_and_related_labels(self):
        for query, expected in (
            ('vpn-gateway', [self.first]),
            ('Dell', [self.first]),
            ('staging', [self.second]),
            ('Ubuntu', [self.first]),
            ('finance-db', [self.second]),
            ('production', [self.first, self.third]),
            ('windows', [self.second, self.third]),
        ):
            actual, _ = self.matches(query)
            ordering = sorted(
                expected, key=lambda asset: (
                    asset.cluster_id, asset.server_name, asset.pk,
                ),
            )
            self.assertEqual(actual, [asset.pk for asset in ordering], query)

    def test_multi_field_match_does_not_duplicate_one_asset(self):
        asset = Server.objects.create(
            server_name='Dell Production', cluster=self.first.cluster,
            vendor=self.first.vendor, os=self.first.os,
            pub_date=timezone.now(),
        )
        ids, _ = self.matches('Dell')
        self.assertEqual(ids.count(asset.pk), 1)
        self.assertEqual(len(ids), 2)

    def test_empty_and_unmatched_searches_do_not_show_inventory(self):
        for query in ('', '  ', 'this-does-not-exist'):
            ids, response = self.matches(query)
            self.assertEqual(ids, [])
            self.assertContains(response, 'No systems are available.')

    def test_search_hint_and_value_are_accessible(self):
        _, response = self.matches('Dell')
        self.assertContains(response, 'Search systems by name, vendor, cluster or OS')
        self.assertContains(response, 'value="Dell"')

    def test_search_preserves_authentication_and_permission_boundaries(self):
        self.client.logout()
        self.assertEqual(
            self.client.get(reverse('inventory:search'), {'q': 'Dell'}).status_code,
            302,
        )
        self.client.force_login(self.other)
        self.assertEqual(
            self.client.get(reverse('inventory:search'), {'q': 'Dell'}).status_code,
            403,
        )
