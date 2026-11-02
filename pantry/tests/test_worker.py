from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone

from pantry.models import Notification, ReminderJob, ReminderSubscription
from pantry.tests.factories import kitchen
from pantry.worker import MAX_ATTEMPTS, claim_job, fail_job, finish_job, process_one


class ReminderWorkerTests(TestCase):
    def setUp(self):
        _, home = kitchen()
        self.member = home.memberships.get()
        self.subscription = ReminderSubscription.objects.create(
            membership=self.member, enabled=True
        )
        self.now = timezone.now()
        self.job = ReminderJob.objects.create(
            membership=self.member,
            local_date=self.now.date(),
            payload={"total": 1},
            available_at=self.now,
        )

    def test_acknowledged_job_delivers_only_once(self):
        claim = claim_job(self.now)
        self.assertEqual(finish_job(claim, self.now), "sent")
        self.assertEqual(finish_job(claim, self.now), "stale")
        self.assertEqual(Notification.objects.count(), 1)
        self.assertIsNone(claim_job(self.now))

    def test_crashed_worker_lease_is_recovered_and_old_ack_is_fenced(self):
        old = claim_job(self.now)
        later = self.now + timedelta(minutes=3)
        new = claim_job(later)
        self.assertNotEqual(old.lease_token, new.lease_token)
        self.assertEqual(finish_job(old, later), "stale")
        self.assertEqual(fail_job(old, RuntimeError("private"), later), 0)
        self.assertEqual(finish_job(new, later), "sent")
        self.assertEqual(Notification.objects.count(), 1)

    def test_delivery_failure_rolls_back_inbox_and_backs_off(self):
        def partial_failure(job):
            Notification.objects.create(job=job, membership=job.membership)
            raise RuntimeError("private information")

        with patch("pantry.worker.deliver_inbox", side_effect=partial_failure):
            self.assertEqual(process_one(self.now), "failed")
        self.assertFalse(Notification.objects.exists())
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "pending")
        self.assertEqual(self.job.last_error, "RuntimeError")
        self.assertIsNone(claim_job(self.now + timedelta(seconds=29)))
        self.assertEqual(process_one(self.now + timedelta(seconds=31)), "sent")

    def test_retry_limit_is_terminal_even_after_worker_crashes(self):
        self.job.attempts = MAX_ATTEMPTS - 1
        self.job.save()
        claim_job(self.now)
        self.assertIsNone(claim_job(self.now + timedelta(minutes=3)))
        self.job.refresh_from_db()
        self.assertEqual(self.job.status, "dead")

    def test_opt_out_before_delivery_cancels_pending_work(self):
        claim = claim_job(self.now)
        self.subscription.enabled = False
        self.subscription.save()
        self.assertEqual(finish_job(claim, self.now), "cancelled")
        self.assertFalse(Notification.objects.exists())
