from io import StringIO

from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from inventory.models import Cluster, Operating_System, Server, Vendor


class HistoricalSystemNameAuditTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.os = Operating_System.objects.create(os_name="Ubuntu")
        cls.vendor = Vendor.objects.create(vendor_name="Vendor")
        cls.first_cluster = Cluster.objects.create(cluster_name="Primary")
        cls.second_cluster = Cluster.objects.create(cluster_name="Secondary")

    def make_system(self, name, cluster=None):
        return Server.objects.create(
            server_name=name,
            os=self.os,
            vendor=self.vendor,
            cluster=cluster or self.first_cluster,
            pub_date=timezone.now(),
        )

    def audit(self, *args):
        output = StringIO()
        call_command("audit_asset_names", *args, stdout=output)
        return output.getvalue()

    def test_empty_inventory_reports_no_issues(self):
        output = self.audit("--fail-on-issues")
        self.assertIn("Systems examined: 0", output)
        self.assertIn("Duplicate cluster/name groups: 0", output)

    def test_identifies_case_and_whitespace_duplicates_without_writing(self):
        first = self.make_system("VPN-Gateway")
        second = self.make_system(" vpn-gateway ")
        third = self.make_system("   ")
        another_cluster = self.make_system("VPN-Gateway", self.second_cluster)
        before = list(Server.objects.order_by("pk").values_list(
            "pk", "server_name", "cluster_id",
        ))
        output = self.audit("--show-record-ids")
        self.assertIn("Systems examined: 4", output)
        self.assertIn("Blank system names: 1", output)
        self.assertIn("Names with outer whitespace: 1", output)
        self.assertIn("Duplicate cluster/name groups: 1", output)
        self.assertIn("Records within duplicate groups: 2", output)
        self.assertIn(str(first.pk), output)
        self.assertIn(str(second.pk), output)
        self.assertIn(str(third.pk), output)
        self.assertNotIn("VPN-Gateway", output)
        self.assertEqual(before, list(Server.objects.order_by("pk").values_list(
            "pk", "server_name", "cluster_id",
        )))
        self.assertTrue(Server.objects.filter(pk=another_cluster.pk).exists())

    def test_default_audit_hides_identifiers_and_names(self):
        self.make_system("Sensitive internal hostname ")
        output = self.audit()
        self.assertNotIn("Sensitive internal hostname", output)
        self.assertNotIn("Cluster ID", output)
        self.assertIn("Names with outer whitespace: 1", output)

    def test_fail_on_issues_is_opt_in(self):
        self.make_system(" ")
        self.audit()
        with self.assertRaises(SystemExit) as raised:
            self.audit("--fail-on-issues")
        self.assertEqual(raised.exception.code, 1)

    def test_same_name_in_other_clusters_is_not_duplicate(self):
        self.make_system("edge-01")
        self.make_system("EDGE-01", self.second_cluster)
        output = self.audit("--fail-on-issues")
        self.assertIn("Duplicate cluster/name groups: 0", output)
