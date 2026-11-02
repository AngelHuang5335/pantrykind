from django.core.management.base import BaseCommand

from pantry.reminders import enqueue_reminders


class Command(BaseCommand):
    help = "Enqueue due opt-in inbox reminders. Safe to run every minute."

    def handle(self, *args, **options):
        self.stdout.write(f"Enqueued {enqueue_reminders()} reminder(s).")
