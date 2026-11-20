"""End-to-end synthetic SQLite snapshot -> isolated Django restore checks."""
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest

from scripts.sqlite_backup import backup

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "django_restore_smoke.py"


class DjangoRestoreSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="servdesk-restore-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.live = self.root / "source.sqlite3"
        self.snapshot = self.root / "snapshot.sqlite3"
        self.env = {**os.environ, "DJANGO_DB_PATH": str(self.live),
                    "DJANGO_DEBUG": "true",
                    "DJANGO_SECRET_KEY": "synthetic-test-only",
                    "DJANGO_SETTINGS_MODULE": "tickets.settings"}

    def command(self, *args):
        return subprocess.run(
            [sys.executable, *map(str, args)], cwd=ROOT,
            env=self.env, text=True, capture_output=True, timeout=120,
        )

    def test_snapshot_restores_django_models_and_preserves_original(self):
        migrate = self.command("manage.py", "migrate", "--noinput")
        self.assertEqual(migrate.returncode, 0, migrate.stdout + migrate.stderr)
        fixture = """from django.utils import timezone
from django.contrib.auth import get_user_model
from issues.models import Issue, Priority
from inventory.models import Vendor, Cluster, Operating_System, Server
from knowledgebase.models import Article
from projects.models import Project
u=get_user_model().objects.create_user(username='synthetic-operator')
p=Priority.objects.create(name='Test')
i=Issue.objects.create(requestor_name='tester',summary='Fixture',description='Private test fixture',priority=p,pub_date=timezone.now(),assigned=u)
v=Vendor.objects.create(vendor_name='Fixture vendor')
c=Cluster.objects.create(cluster_name='Fixture cluster')
o=Operating_System.objects.create(os_name='Fixture OS')
Server.objects.create(server_name='Fixture host',vendor=v,cluster=c,os=o,pub_date=timezone.now())
Article.objects.create(author='tester',description='Fixture article',keywords='fixture',pub_date=timezone.now(),source_issue=i)
Project.objects.create(requestor_name='tester',summary='Fixture',description='Project',pub_date=timezone.now(),assigned=u)
"""
        seed = self.command("manage.py", "shell", "-c", fixture)
        self.assertEqual(seed.returncode, 0, seed.stdout + seed.stderr)
        backup(self.live, self.snapshot)
        original = self.live.read_bytes()
        proc = self.command(SCRIPT, "--snapshot", self.snapshot)
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
        self.assertIn("rehearsal passed", proc.stdout)
        self.assertEqual(self.live.read_bytes(), original)
        self.assertTrue(self.snapshot.exists())

    def test_unmigrated_sqlite_database_is_rejected_without_writes(self):
        with sqlite3.connect(self.live) as db:
            db.execute("CREATE TABLE test_only(id INTEGER)")
        backup(self.live, self.snapshot)
        original = self.snapshot.read_bytes()
        proc = self.command(SCRIPT, "--snapshot", self.snapshot)
        self.assertNotEqual(proc.returncode, 0)
        self.assertEqual(self.snapshot.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
