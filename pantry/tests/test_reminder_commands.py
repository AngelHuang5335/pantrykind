import json
from io import StringIO

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase
from django.utils import timezone

from pantry.models import ReminderJob, ReminderSubscription
from pantry.tests.factories import kitchen


class ReminderCommandTests(TestCase):
    def setUp(self):
        _, home = kitchen()
        member = home.memberships.get()
        self.subscription = ReminderSubscription.objects.create(membership=member, enabled=True)
        self.job = ReminderJob.objects.create(
            membership=member, local_date=timezone.localdate(), payload={"private": "do-not-log"}
        )

    def command(self, name, *args, **kwargs):
        output = StringIO()
        call_command(name, *args, stdout=output, **kwargs)
        return output.getvalue()

    def test_bounded_worker_drains_and_reports_counts(self):
        self.assertEqual(json.loads(self.command("reminder_worker", limit=1)), {"sent": 1})
        self.assertEqual(json.loads(self.command("reminder_worker", limit=1)), {})

    def test_status_never_includes_payload_or_account(self):
        text = self.command("reminder_status")
        self.assertNotIn("do-not-log", text)
        self.assertEqual(json.loads(text)["counts"], {"pending": 1})

    def test_retry_only_restarts_dead_and_opted_in_jobs(self):
        with self.assertRaises(CommandError):
            self.command("retry_reminder", self.job.pk)
        self.job.status = "dead"
        self.job.save()
        self.command("retry_reminder", self.job.pk)
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "pending")
        self.job.status = "dead"
        self.job.save()
        self.subscription.enabled = False
        self.subscription.save()
        with self.assertRaises(CommandError):
            self.command("retry_reminder", self.job.pk)
