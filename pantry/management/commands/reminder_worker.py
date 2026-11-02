import json
from collections import Counter

from django.core.management.base import BaseCommand, CommandError

from pantry.worker import process_one


class Command(BaseCommand):
    help = "Drain a bounded batch of due inbox jobs, then exit; schedule this every minute."

    def add_arguments(self, parser):
        parser.add_argument("--limit", type=int, default=100)

    def handle(self, *args, **options):
        if not 1 <= options["limit"] <= 10000:
            raise CommandError("Limit must be between 1 and 10000.")
        counts = Counter()
        for _ in range(options["limit"]):
            result = process_one()
            if result == "empty":
                break
            counts[result] += 1
        self.stdout.write(json.dumps(dict(counts), sort_keys=True))
