from decimal import Decimal
from uuid import uuid4
from django.core.exceptions import ValidationError
from django.test import TestCase
from pantry.models import Item, StockEvent
from pantry.services import record_stock
from pantry.tests.factories import kitchen


class StockTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.item = Item.objects.create(household=self.home, name="Rice", quantity=2, unit="kg")

    def action(self, amount, kind="used", key=None):
        return record_stock(
            household=self.home,
            item_id=self.item.pk,
            actor=self.user,
            kind=kind,
            amount=amount,
            request_id=key or uuid4(),
        )

    def test_subtract_and_record(self):
        self.action(".25")
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("1.750"))
        self.assertEqual(StockEvent.objects.count(), 1)

    def test_overdraw_rolls_back(self):
        with self.assertRaises(ValidationError):
            self.action(3)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 2)
        self.assertFalse(StockEvent.objects.exists())

    def test_repeated_request_is_not_double_counted(self):
        key = uuid4()
        self.action(1, key=key)
        self.action(1, key=key)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)

    def test_nonfinite_and_precision_are_rejected(self):
        for amount in ["NaN", "Infinity", "0", "-1", ".0001"]:
            with self.assertRaises(ValidationError):
                self.action(amount)

    def test_foreign_household_is_rejected(self):
        user, other = kitchen("other")
        with self.assertRaises(Item.DoesNotExist):
            record_stock(
                household=other,
                item_id=self.item.pk,
                actor=user,
                kind="used",
                amount=1,
                request_id=uuid4(),
            )


class StockActionViewTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.client.force_login(self.user)
        self.item = Item.objects.create(household=self.home, name="Oats", quantity=2)

    def test_get_never_consumes_stock(self):
        self.client.get(f"/pantry/{self.item.pk}/action/used/")
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 2)

    def test_action_form_records_usage(self):
        self.client.post(
            f"/pantry/{self.item.pk}/action/used/",
            {"amount": "1", "request_id": str(uuid4())},
        )
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)


class RestockTests(StockTests):
    def test_restock_increases_quantity(self):
        self.action(".5", kind="restocked")
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, Decimal("2.500"))


class WasteTests(TestCase):
    def test_discard_requires_a_reason(self):
        user, home = kitchen()
        self.client.force_login(user)
        item = Item.objects.create(household=home, name="Milk", quantity=1)
        response = self.client.post(
            f"/pantry/{item.pk}/action/wasted/",
            {"amount": 1, "request_id": str(uuid4())},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(StockEvent.objects.exists())


class LedgerIntegrityTests(TestCase):
    def test_edit_cannot_silently_rewrite_stock_or_units(self):
        user, home = kitchen()
        self.client.force_login(user)
        item = Item.objects.create(household=home, name="Rice", quantity=2, unit="kg")
        record_stock(
            household=home,
            item_id=item.pk,
            actor=user,
            kind="used",
            amount=1,
            request_id=uuid4(),
        )
        self.client.post(
            f"/pantry/{item.pk}/edit/",
            {
                "name": "Rice",
                "category": "grains",
                "location": "pantry",
                "quantity": 99,
                "unit": "g",
                "low_stock_at": 0,
            },
        )
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.unit, "kg")
