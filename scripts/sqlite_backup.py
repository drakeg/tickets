"""Non-destructive SQLite backup and isolated restore integrity verification.

Only uses the Python standard library. The source database is opened read-only.
Backups never overwrite existing destinations, and verification only copies the
snapshot into a temporary directory; it never touches the live database.
"""
import argparse
import os
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from urllib.parse import quote


def _read_only(db_path):
    uri = "file:" + quote(str(db_path), safe="/") + "?mode=ro"
    return sqlite3.connect(uri, uri=True, timeout=15)


def _integrity_check(db_path):
    with _read_only(db_path) as connection:
        result = connection.execute("PRAGMA integrity_check").fetchone()
        if not result or result[0] != "ok":
            raise ValueError("SQLite integrity verification failed")


def backup(source, destination):
    source = Path(source).expanduser().resolve(strict=True)
    destination = Path(destination).expanduser().absolute()
    if not source.is_file():
        raise ValueError("Source is not a regular file")
    if source == destination or source.samefile(destination) if destination.exists() else source == destination:
        raise ValueError("Source and destination must be different")
    if not destination.parent.is_dir():
        raise ValueError("Destination parent directory must already exist")

    # O_EXCL prevents accidental snapshot replacement even with concurrent runs.
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    os.close(fd)
    try:
        with _read_only(source) as input_db:
            with sqlite3.connect(destination) as output_db:
                input_db.backup(output_db)
        verify(destination)
    except BaseException:
        destination.unlink(missing_ok=True)
        raise
    return destination


def verify(snapshot):
    snapshot = Path(snapshot).expanduser().resolve(strict=True)
    if not snapshot.is_file():
        raise ValueError("Snapshot is not a regular file")
    # Rehearse restoring into an isolated location, never over the source.
    with tempfile.TemporaryDirectory(prefix="tickets-restore-") as directory:
        restored = Path(directory) / "restored.sqlite3"
        shutil.copyfile(snapshot, restored)
        _integrity_check(restored)
        with _read_only(restored) as connection:
            # Proves the restored file contains a readable SQLite schema.
            connection.execute("SELECT name FROM sqlite_master LIMIT 1").fetchall()
    return True


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("backup")
    create.add_argument("--source", required=True)
    create.add_argument("--output", required=True)
    check = commands.add_parser("verify")
    check.add_argument("--snapshot", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "backup":
            path = backup(args.source, args.output)
            print("Backup created and isolated restore verified:", path)
        else:
            verify(args.snapshot)
            print("Isolated SQLite restore integrity check passed")
    except (OSError, ValueError, sqlite3.Error) as error:
        parser.exit(1, f"Backup verification error: {error}\n")


if __name__ == "__main__":
    main()
