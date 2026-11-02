import hashlib
import sqlite3
import tempfile
from contextlib import closing
from io import StringIO
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, override_settings

from pantry.backups import REQUIRED_TABLES, inspect_backup


class RestoreTests(SimpleTestCase):
    def fixture(self, path):
        with closing(sqlite3.connect(path)) as db:
            for table in REQUIRED_TABLES:
                db.execute(f'CREATE TABLE "{table}" (id INTEGER PRIMARY KEY)')
            db.execute("INSERT INTO pantry_household VALUES (1)")
            db.execute("INSERT INTO pantry_item VALUES (1)")
            db.commit()

    def test_restore_verifies_copy_without_changing_source_or_live(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, dest, live = (
                root / "backup.sqlite3",
                root / "restored.sqlite3",
                root / "live.sqlite3",
            )
            self.fixture(source)
            before = hashlib.sha256(source.read_bytes()).digest()
            with override_settings(
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": live}}
            ):
                call_command("restore_pantry", str(source), str(dest), stdout=StringIO())
                with self.assertRaises(CommandError):
                    call_command("restore_pantry", str(source), str(dest), stdout=StringIO())
                with self.assertRaises(CommandError):
                    call_command("restore_pantry", str(source), str(live), stdout=StringIO())
            self.assertFalse(live.exists())
            self.assertEqual(hashlib.sha256(source.read_bytes()).digest(), before)
            self.assertEqual(inspect_backup(dest)["items"], 1)

    def test_foreign_database_or_corrupt_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.sqlite3"
            path.write_bytes(b"not a database")
            with self.assertRaises(CommandError):
                inspect_backup(path)
            path.unlink()
            with closing(sqlite3.connect(path)) as db:
                db.execute("CREATE TABLE other (id INTEGER)")
            with self.assertRaises(CommandError):
                inspect_backup(path)

    def test_broken_foreign_key_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "broken.sqlite3"
            self.fixture(path)
            with closing(sqlite3.connect(path)) as db:
                db.execute("CREATE TABLE orphan (parent INTEGER REFERENCES pantry_household(id))")
                db.execute("INSERT INTO orphan VALUES (999)")
                db.commit()
            with self.assertRaises(CommandError):
                inspect_backup(path)
