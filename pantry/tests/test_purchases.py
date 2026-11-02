from datetime import date
from unittest.mock import patch
from uuid import uuid4

from django.core.exceptions import ValidationError
from django.test import TestCase

from pantry.models import Item, PurchaseReceipt, ShoppingEntry, StockEvent
from pantry.services import add_to_shopping, purchase_shopping
from pantry.tests.factories import kitchen


class PurchaseTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.entry = add_to_shopping(self.home, "Rice", 3, "kg")

    def buy(self, **overrides):
        data = dict(
            household=self.home,
            actor=self.user,
            entry_id=self.entry.pk,
            amount=1,
            request_id=uuid4(),
            expiry_date=date(2030, 1, 1),
        )
        return purchase_shopping(**(data | overrides))

    def test_partial_purchase_creates_ledger_and_leaves_remainder(self):
        receipt = self.buy()
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.quantity, 2)
        self.assertFalse(self.entry.checked)
        self.assertEqual(receipt.item.quantity, 1)
        self.assertEqual(receipt.item.expiry_date, date(2030, 1, 1))
        self.assertEqual(StockEvent.objects.get().amount, 1)

    def test_full_purchase_checks_list_and_survives_clearing_it(self):
        key = uuid4()
        first = self.buy(amount=3, request_id=key)
        self.entry.refresh_from_db()
        self.assertTrue(self.entry.checked)
        self.entry.delete()
        self.assertEqual(self.buy(amount=3, entry_id=first.source_entry_id, request_id=key), first)
        self.assertEqual(Item.objects.count(), 1)

    def test_oversized_purchase_has_no_side_effects(self):
        with self.assertRaises(ValidationError):
            self.buy(amount=4)
        self.assertFalse(Item.objects.exists())
        self.assertFalse(PurchaseReceipt.objects.exists())

    def test_failure_rolls_back_batch_list_and_receipt_together(self):
        with patch("pantry.services.record_stock", side_effect=RuntimeError("storage failure")):
            with self.assertRaises(RuntimeError):
                self.buy()
        self.assertFalse(Item.objects.exists())
        self.assertFalse(PurchaseReceipt.objects.exists())
        self.entry.refresh_from_db()
        self.assertEqual(self.entry.quantity, 3)

    def test_changed_payload_cannot_reuse_receipt(self):
        key = uuid4()
        self.buy(request_id=key)
        with self.assertRaises(ValidationError):
            self.buy(request_id=key, amount=2)

    def test_foreign_entry_cannot_be_purchased(self):
        _, foreign = kitchen("foreign")
        entry = add_to_shopping(foreign, "Private rice", 3, "kg")
        with self.assertRaises(ShoppingEntry.DoesNotExist):
            self.buy(entry_id=entry.pk)
