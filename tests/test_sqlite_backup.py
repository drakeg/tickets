"""Tests operate only on temporary synthetic SQLite files."""
import os
from pathlib import Path
import sqlite3
import tempfile
import unittest

from scripts.sqlite_backup import backup, verify


class BackupRehearsalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.live = self.root / "live.sqlite3"
        with sqlite3.connect(self.live) as conn:
            conn.execute("CREATE TABLE records (id INTEGER PRIMARY KEY, value TEXT)")
            conn.execute("INSERT INTO records(value) VALUES ('ticket')")
        self.snapshot = self.root / "snapshot.sqlite3"

    def test_preserves_source_and_restores_committed_rows(self):
        original = self.live.read_bytes()
        backup(self.live, self.snapshot)
        self.assertEqual(self.live.read_bytes(), original)
        self.assertTrue(verify(self.snapshot))
        with sqlite3.connect(self.snapshot) as conn:
            self.assertEqual(conn.execute("SELECT value FROM records").fetchone()[0], "ticket")

    def test_does_not_overwrite_existing_snapshot(self):
        self.snapshot.write_bytes(b"preserve me")
        with self.assertRaises(FileExistsError):
            backup(self.live, self.snapshot)
        self.assertEqual(self.snapshot.read_bytes(), b"preserve me")

    def test_rejects_source_equal_to_destination(self):
        with self.assertRaises(ValueError):
            backup(self.live, self.live)
        self.assertTrue(self.live.exists())

    def test_missing_source_never_creates_destination(self):
        with self.assertRaises(FileNotFoundError):
            backup(self.root / "missing.db", self.snapshot)
        self.assertFalse(self.snapshot.exists())

    def test_corrupt_snapshot_is_rejected(self):
        self.snapshot.write_bytes(b"not a sqlite database")
        with self.assertRaises(sqlite3.DatabaseError):
            verify(self.snapshot)

    def test_new_backup_is_private_on_posix(self):
        backup(self.live, self.snapshot)
        if os.name == "posix":
            self.assertEqual(self.snapshot.stat().st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
