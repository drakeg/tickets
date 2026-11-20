"""Verify a ServDesk SQLite snapshot against Django in a disposable directory.

Never writes to the supplied snapshot or the live configured database. This is
an application/schema-read smoke test, not a full interactive restore drill.
"""
import argparse
import io
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile

from scripts.sqlite_backup import _integrity_check


def rehearse(snapshot):
    snapshot = Path(snapshot).expanduser().resolve(strict=True)
    if not snapshot.is_file():
        raise ValueError("Snapshot must be a regular file")
    with tempfile.TemporaryDirectory(prefix="servdesk-django-restore-") as temp:
        restored = Path(temp) / "isolated.sqlite3"
        shutil.copyfile(snapshot, restored)
        _integrity_check(restored)

        # Set the DB path before importing Django settings or ORM models.
        os.environ["DJANGO_DB_PATH"] = str(restored)
        os.environ.setdefault("DJANGO_DEBUG", "true")
        os.environ.setdefault("DJANGO_SECRET_KEY", "temporary-restore-check-only")
        os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tickets.settings")
        import django
        django.setup()

        from django.conf import settings
        from django.core.management import call_command
        from django.db import connection
        from django.db.migrations.executor import MigrationExecutor
        from django.contrib.auth import get_user_model
        from inventory.models import Server
        from issues.models import Issue, IssueChange, Priority
        from knowledgebase.models import Article
        from projects.models import Project

        if Path(settings.DATABASES["default"]["NAME"]).resolve() != restored.resolve():
            raise RuntimeError("Refusing to inspect a non-isolated database")
        call_command("check", stdout=io.StringIO())
        executor = MigrationExecutor(connection)
        pending = executor.migration_plan(executor.loader.graph.leaf_nodes())
        if pending:
            raise RuntimeError("Restored snapshot has unapplied Django migrations")
        with connection.cursor() as cursor:
            cursor.execute("PRAGMA foreign_key_check")
            if cursor.fetchone():
                raise RuntimeError("Restored snapshot has broken foreign keys")

        # Exercise real ORM queries and key joins without printing record details.
        for model in (get_user_model(), Priority, IssueChange):
            model.objects.exists()
        for queryset in (
            Issue.objects.select_related("priority", "assigned"),
            Project.objects.select_related("assigned"),
            Server.objects.select_related("os", "vendor", "cluster"),
            Article.objects.select_related("source_issue"),
        ):
            list(queryset[:1])
        connection.close()
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", required=True)
    args = parser.parse_args(argv)
    try:
        rehearse(args.snapshot)
    except (OSError, sqlite3.Error, ValueError, RuntimeError) as error:
        parser.exit(1, f"Restore rehearsal failed: {error}\n")
    print("Isolated Django schema, migrations and ORM restore rehearsal passed")


if __name__ == "__main__":
    main()
