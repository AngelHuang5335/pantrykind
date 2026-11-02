import json

from django.core.management.base import BaseCommand
from django.db.models import Count, Min
from django.utils import timezone

from pantry.models import ReminderJob


class Command(BaseCommand):
    help = "Print private operator queue metrics without food names, recipients or payloads."

    def handle(self, *args, **options):
        rows = ReminderJob.objects.values("status").annotate(count=Count("pk"))
        oldest = ReminderJob.objects.filter(status="pending").aggregate(value=Min("available_at"))[
            "value"
        ]
        result = {
            "counts": {row["status"]: row["count"] for row in rows},
            "oldest_due_seconds": max(0, int((timezone.now() - oldest).total_seconds()))
            if oldest
            else 0,
        }
        self.stdout.write(json.dumps(result, sort_keys=True))
