import tempfile, sqlite3
from contextlib import closing
from pathlib import Path
from io import StringIO
from django.test import SimpleTestCase, override_settings
from django.core.management import call_command
from django.core.management.base import CommandError


class BackupTests(SimpleTestCase):
    def test_backup_is_consistent_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.sqlite3"
            dest = Path(directory) / "backup.sqlite3"
            with closing(sqlite3.connect(source)) as db:
                db.execute("CREATE TABLE sample (value TEXT)")
                db.execute("INSERT INTO sample VALUES ('keep me')")
                db.commit()
            with override_settings(
                DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": source}}
            ):
                call_command("backup_pantry", str(dest), stdout=StringIO())
                with self.assertRaises(CommandError):
                    call_command("backup_pantry", str(dest), stdout=StringIO())
            with closing(sqlite3.connect(dest)) as db:
                self.assertEqual(db.execute("SELECT value FROM sample").fetchone()[0], "keep me")
