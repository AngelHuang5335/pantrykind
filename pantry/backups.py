"""Inspect SQLite snapshots read-only, before making a separate restore candidate."""

import sqlite3
from contextlib import closing
from pathlib import Path

from django.core.management.base import CommandError

REQUIRED_TABLES = {
    "auth_user",
    "django_migrations",
    "pantry_household",
    "pantry_membership",
    "pantry_item",
}


def inspect_backup(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise CommandError("Backup file does not exist.")
    try:
        with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True)) as db:
            if db.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
                raise CommandError("Backup failed SQLite integrity checks.")
            if db.execute("PRAGMA foreign_key_check").fetchone():
                raise CommandError("Backup contains broken foreign-key references.")
            tables = {
                row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")
            }
            if not REQUIRED_TABLES <= tables:
                raise CommandError("Backup is not a PantryKind account database.")
            return {
                "households": db.execute("SELECT COUNT(*) FROM pantry_household").fetchone()[0],
                "items": db.execute("SELECT COUNT(*) FROM pantry_item").fetchone()[0],
                "migrations": db.execute("SELECT COUNT(*) FROM django_migrations").fetchone()[0],
            }
    except sqlite3.Error:
        raise CommandError("Backup is unreadable or is not a valid SQLite database.") from None
