# SQLite backup and isolated restore rehearsal

The local ServDesk database lives in the Docker Compose `tickets_data` named
volume at `/data/db.sqlite3`. **Never** use `docker compose down -v` when
preserving test or customer data.

## Create a snapshot without stopping Django

From the Tickets checkout on your Mac, after updating to a revision with the
backup script:

```bash
mkdir -p backups
STAMP=$(date -u +%Y%m%dT%H%M%SZ)
docker compose exec -T web python scripts/sqlite_backup.py backup \
  --source /data/db.sqlite3 --output "/tmp/tickets-$STAMP.sqlite3"
docker compose cp "web:/tmp/tickets-$STAMP.sqlite3" "./backups/tickets-$STAMP.sqlite3"
chmod 600 "./backups/tickets-$STAMP.sqlite3"
python3 scripts/sqlite_backup.py verify \
  --snapshot "./backups/tickets-$STAMP.sqlite3"
```

Only after checking the local snapshot exists and passes verification, remove
the temporary copy **in the container**, not the persistent database:

```bash
docker compose exec -T web rm "/tmp/tickets-$STAMP.sqlite3"
```

The script uses SQLite's online backup API, refusing to overwrite an existing
snapshot and never opening the live database for writes. The verification step
copies the snapshot into a temporary directory, checks SQLite integrity and
reads its schema. Neither action overwrites an existing database.

## Recovery and limitations

This is an isolated *database integrity rehearsal*, **not** a claim that the
whole Django application has been restored or that its login, assets, or
knowledge-base flows work. Keep encrypted off-device backups for real recovery.
Record snapshot time, source commit, environment, verification outcome and
location in an operator runbook; never commit customer backups to GitHub.

A real restore requires an approved maintenance window, a separate service and
volume, migrations compatible with the snapshot, and workflow verification.
Do not overwrite `/data/db.sqlite3` on a running instance. Restore drills and
retention/deletion policy remain follow-up tasks.

## Automated validation

```bash
python3 -m unittest discover -s tests -p 'test_sqlite_backup.py' -v
```

All test records are synthetic SQLite data created in temporary directories.
