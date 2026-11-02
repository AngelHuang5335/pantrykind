from django.test import TestCase
from django.utils import timezone

from pantry.models import Notification, ReminderJob, ReminderSubscription
from pantry.tests.factories import kitchen
from pantry.worker import claim_job, finish_job


class ReminderPrivacyTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.member = self.home.memberships.get()
        self.client.force_login(self.user)
        self.sub = ReminderSubscription.objects.create(membership=self.member, enabled=True)
        self.job = ReminderJob.objects.create(
            membership=self.member,
            local_date=timezone.localdate(),
            payload={"total": 1, "items": [{"name": "My oats"}]},
        )

    def test_get_never_creates_preferences_or_notifications(self):
        self.sub.delete()
        self.assertEqual(self.client.get("/inbox/").status_code, 200)
        self.assertFalse(ReminderSubscription.objects.exists())
        self.assertFalse(Notification.objects.exists())

    def test_opt_out_fences_an_inflight_delivery(self):
        claim = claim_job()
        self.assertEqual(self.client.post("/inbox/", {"local_hour": 9}).status_code, 302)
        self.assertEqual(finish_job(claim), "stale")
        self.assertFalse(Notification.objects.exists())

    def test_other_members_cannot_read_or_mark_private_inbox(self):
        notification = Notification.objects.create(
            job=self.job, membership=self.member, payload=self.job.payload
        )
        user, _ = kitchen("other")
        self.client.force_login(user)
        self.assertNotContains(self.client.get("/inbox/"), "My oats")
        self.assertEqual(self.client.post(f"/inbox/{notification.pk}/read/").status_code, 404)

    def test_read_action_is_post_only_and_idempotent(self):
        notification = Notification.objects.create(job=self.job, membership=self.member)
        url = f"/inbox/{notification.pk}/read/"
        self.assertEqual(self.client.get(url).status_code, 405)
        self.client.post(url)
        notification.refresh_from_db()
        first = notification.read_at
        self.client.post(url)
        notification.refresh_from_db()
        self.assertEqual(notification.read_at, first)
