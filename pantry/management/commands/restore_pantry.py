import os
import sqlite3
from contextlib import closing
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from pantry.backups import inspect_backup


class Command(BaseCommand):
    help = (
        "Restore SQLite into a NEW offline candidate. Never writes to the configured live database."
    )

    def add_arguments(self, parser):
        parser.add_argument("source")
        parser.add_argument("destination")

    def handle(self, *args, **options):
        source = Path(options["source"]).resolve()
        destination = Path(options["destination"]).resolve()
        if settings.DATABASES["default"]["ENGINE"] != "django.db.backends.sqlite3":
            raise CommandError("Use pg_restore for PostgreSQL. This command is SQLite only.")
        live = Path(settings.DATABASES["default"]["NAME"]).resolve()
        if destination == live or destination == source or destination.exists():
            raise CommandError("Choose a new offline destination, distinct from the live database.")
        inspect_backup(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        created = False
        try:
            descriptor = os.open(destination, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
            created = True
            with closing(sqlite3.connect(source.as_uri() + "?mode=ro", uri=True)) as src:
                with closing(sqlite3.connect(destination)) as dest:
                    src.backup(dest)
            counts = inspect_backup(destination)
        except Exception:
            if created:
                destination.unlink(missing_ok=True)
            raise
        self.stdout.write(
            f"Verified offline restore: {counts['households']} kitchens, {counts['items']} batches."
        )
