"""Report historical system naming problems without modifying database records."""
from collections import defaultdict

from django.core.management.base import BaseCommand

from inventory.models import Server


class Command(BaseCommand):
    help = (
        "Read-only audit of blank, untrimmed and duplicate system names within "
        "each cluster. Does not change records."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--show-record-ids", action="store_true",
            help="Show affected system IDs and cluster IDs (never names).",
        )
        parser.add_argument(
            "--fail-on-issues", action="store_true",
            help="Exit nonzero if issues exist, for explicit operator checks.",
        )

    def handle(self, *args, **options):
        blank_ids = []
        untrimmed_ids = []
        groups = defaultdict(list)
        examined = 0

        for system_id, cluster_id, name in Server.objects.order_by("pk").values_list(
            "pk", "cluster_id", "server_name",
        ).iterator():
            examined += 1
            normalized = (name or "").strip()
            if not normalized:
                blank_ids.append(system_id)
                continue
            if normalized != name:
                untrimmed_ids.append(system_id)
            groups[(cluster_id, normalized.casefold())].append(system_id)

        duplicates = {
            key: ids for key, ids in groups.items() if len(ids) > 1
        }
        count_duplicates = sum(len(ids) for ids in duplicates.values())
        count_issues = len(blank_ids) + len(untrimmed_ids) + count_duplicates

        self.stdout.write(f"Systems examined: {examined}")
        self.stdout.write(f"Blank system names: {len(blank_ids)}")
        self.stdout.write(f"Names with outer whitespace: {len(untrimmed_ids)}")
        self.stdout.write(f"Duplicate cluster/name groups: {len(duplicates)}")
        self.stdout.write(f"Records within duplicate groups: {count_duplicates}")
        self.stdout.write("Read-only audit; no database changes made.")

        if options["show_record_ids"]:
            self.stdout.write(f"Blank system IDs: {sorted(blank_ids)}")
            self.stdout.write(f"Whitespace system IDs: {sorted(untrimmed_ids)}")
            for (cluster_id, _), ids in sorted(
                duplicates.items(), key=lambda entry: (entry[0][0], min(entry[1]))
            ):
                self.stdout.write(f"Cluster ID {cluster_id}: duplicate system IDs {ids}")

        if options["fail_on_issues"] and count_issues:
            raise SystemExit(1)
