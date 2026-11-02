from datetime import datetime, timezone as dt_timezone

from django.test import TestCase

from pantry.models import Item, ReminderJob, ReminderSubscription
from pantry.reminders import enqueue_reminders
from pantry.tests.factories import kitchen


class ReminderEnqueueTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.home.timezone_name = "Asia/Shanghai"
        self.home.save()
        self.member = self.home.memberships.get()
        self.subscription = ReminderSubscription.objects.create(
            membership=self.member, enabled=True, local_hour=9
        )
        self.now = datetime(2030, 1, 1, 1, 0, tzinfo=dt_timezone.utc)
        Item.objects.create(household=self.home, name="Oats", expiry_date=self.now.date())

    def test_scheduling_uses_household_hour_and_daily_deduplication(self):
        self.assertEqual(enqueue_reminders(self.now.replace(hour=0)), 0)
        self.assertEqual(enqueue_reminders(self.now), 1)
        self.assertEqual(enqueue_reminders(self.now), 0)
        self.assertEqual(ReminderJob.objects.get().payload["items"][0]["name"], "Oats")

    def test_default_is_opt_out_and_inactive_accounts_are_excluded(self):
        self.subscription.enabled = False
        self.subscription.save()
        self.assertEqual(enqueue_reminders(self.now), 0)
        self.subscription.enabled = True
        self.subscription.save()
        self.user.is_active = False
        self.user.save()
        self.assertEqual(enqueue_reminders(self.now), 0)

    def test_past_date_empty_and_archived_stock_do_not_trigger_reminders(self):
        Item.objects.all().update(quantity=0)
        self.assertEqual(enqueue_reminders(self.now), 0)

    def test_midnight_uses_local_date_not_server_date(self):
        self.subscription.local_hour = 0
        self.subscription.save()
        now = self.now.replace(year=2029, month=12, day=31, hour=16)
        self.assertEqual(enqueue_reminders(now), 1)
        self.assertEqual(ReminderJob.objects.get().local_date.isoformat(), "2030-01-01")
