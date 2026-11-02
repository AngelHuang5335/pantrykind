import os, sqlite3
from contextlib import closing
from pathlib import Path
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create a consistent SQLite backup, including data, users and sessions; never overwrites a file."

    def add_arguments(self, p):
        p.add_argument("destination")

    def handle(self, *args, **options):
        destination = Path(options["destination"]).resolve()
        source = Path(settings.DATABASES["default"]["NAME"]).resolve()
        if not source.is_file():
            raise CommandError("The database does not exist. Run migrations first.")
        if destination == source or destination.exists():
            raise CommandError(
                "Choose a new backup filename; existing files are never overwritten."
            )
        destination.parent.mkdir(parents=True, exist_ok=True)
        created = False
        try:
            descriptor = os.open(str(destination), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(descriptor)
            created = True
            with (
                closing(sqlite3.connect(str(source))) as src,
                closing(sqlite3.connect(str(destination))) as dest,
            ):
                src.backup(dest)
        except Exception as error:
            if created and destination.exists():
                destination.unlink()
            raise CommandError(str(error))
        self.stdout.write(
            self.style.SUCCESS(
                f"Backup saved to {destination}. Keep it private: it contains account data."
            )
        )
