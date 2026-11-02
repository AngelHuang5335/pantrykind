"""Real independent connections; never pretend SQLite emulates row locks."""

from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection, connections
from django.test import TransactionTestCase

from pantry.models import CookLog, Ingredient, Item, Recipe, ShoppingEntry, StockEvent
from pantry.services import add_to_shopping, cook_recipe, record_stock
from pantry.services import purchase_shopping
from pantry.models import PurchaseReceipt, ReminderJob, ReminderSubscription
from pantry.worker import claim_job
from django.utils import timezone
from pantry.tests.factories import kitchen


@skipUnless(connection.vendor == "postgresql", "Requires real PostgreSQL row locks")
class ConcurrentKitchenTests(TransactionTestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.item = Item.objects.create(household=self.home, name="Rice", quantity=1, unit="kg")

    def race(self, operation):
        barrier = Barrier(2, timeout=10)

        def run():
            close_old_connections()
            try:
                barrier.wait()
                return operation()
            except ValidationError:
                return "rejected"
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=2) as pool:
            futures = [pool.submit(run), pool.submit(run)]
            return [future.result(timeout=20) for future in futures]

    def stock(self, key):
        return record_stock(
            household=self.home,
            item_id=self.item.pk,
            actor=self.user,
            kind="used",
            amount=1,
            request_id=key,
        ).pk

    def test_two_distinct_requests_cannot_overdraw(self):
        result = self.race(lambda: self.stock(uuid4()))
        self.assertEqual(result.count("rejected"), 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 0)
        self.assertEqual(StockEvent.objects.count(), 1)

    def test_identical_stock_requests_return_same_receipt(self):
        key = uuid4()
        result = self.race(lambda: self.stock(key))
        self.assertNotIn("rejected", result)
        self.assertEqual(result[0], result[1])
        self.assertEqual(StockEvent.objects.count(), 1)

    def test_identical_cook_requests_wait_then_replay(self):
        recipe = Recipe.objects.create(household=self.home, title="Rice", instructions="Cook.")
        Ingredient.objects.create(recipe=recipe, name="Rice", quantity=1, unit="kg")
        key = uuid4()
        result = self.race(
            lambda: (
                cook_recipe(
                    household=self.home,
                    recipe_id=recipe.pk,
                    actor=self.user,
                    servings=2,
                    request_id=key,
                ).pk
            )
        )
        self.assertNotIn("rejected", result)
        self.assertEqual(result[0], result[1])
        self.assertEqual(CookLog.objects.count(), 1)
        self.assertEqual(StockEvent.objects.count(), 1)

    def test_parallel_shopping_additions_merge_without_lost_updates(self):
        self.race(lambda: add_to_shopping(self.home, "Rice", 1, "kg").pk)
        self.assertEqual(ShoppingEntry.objects.get().quantity, 2)

    def test_identical_purchase_requests_return_one_batch(self):
        entry = add_to_shopping(self.home, "Oats", 1, "pack")
        key = uuid4()
        result = self.race(
            lambda: (
                purchase_shopping(
                    household=self.home,
                    actor=self.user,
                    entry_id=entry.pk,
                    amount=1,
                    request_id=key,
                ).pk
            )
        )
        self.assertEqual(result[0], result[1])
        self.assertNotIn("rejected", result)
        self.assertEqual(PurchaseReceipt.objects.count(), 1)

    def test_parallel_workers_cannot_claim_the_same_job(self):
        member = self.home.memberships.get()
        ReminderSubscription.objects.create(membership=member, enabled=True)
        ReminderJob.objects.create(membership=member, local_date=timezone.localdate())

        def claim():
            job = claim_job()
            return str(job.lease_token) if job else None

        result = self.race(claim)
        self.assertEqual(result.count(None), 1)
