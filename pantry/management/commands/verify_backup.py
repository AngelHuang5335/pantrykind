import json
from django.core.management.base import BaseCommand

from pantry.backups import inspect_backup


class Command(BaseCommand):
    help = "Read-only SQLite integrity, foreign-key and PantryKind schema checks."

    def add_arguments(self, parser):
        parser.add_argument("source")

    def handle(self, *args, **options):
        self.stdout.write(json.dumps(inspect_backup(options["source"]), sort_keys=True))
