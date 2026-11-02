from django.test import TestCase
from pantry.tests.factories import kitchen
from pantry.models import ShoppingEntry


class ShoppingTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.client.force_login(self.user)

    def test_add_entry(self):
        self.client.post("/shopping/", {"name": "Oats", "quantity": "2", "unit": "pack"})
        self.assertEqual(ShoppingEntry.objects.get().household, self.home)

    def test_foreign_entries_are_private(self):
        user, other = kitchen("other")
        ShoppingEntry.objects.create(household=other, name="Private oats")
        self.assertNotContains(self.client.get("/shopping/"), "Private oats")


class ShoppingMergeTests(ShoppingTests):
    def test_case_and_whitespace_merge(self):
        self.client.post("/shopping/", {"name": "Oats", "quantity": 1, "unit": "pack"})
        self.client.post("/shopping/", {"name": "  OATS  ", "quantity": 2, "unit": "pack"})
        self.assertEqual(ShoppingEntry.objects.count(), 1)
        self.assertEqual(ShoppingEntry.objects.get().quantity, 3)

    def test_incompatible_units_do_not_merge(self):
        self.client.post("/shopping/", {"name": "Oats", "quantity": 1, "unit": "pack"})
        self.client.post("/shopping/", {"name": "Oats", "quantity": 2, "unit": "g"})
        self.assertEqual(ShoppingEntry.objects.count(), 2)


class ShoppingToggleTests(ShoppingTests):
    def test_uncheck_merges_with_new_open_entry(self):
        old = ShoppingEntry.objects.create(
            household=self.home, name="Oats", quantity=1, checked=True
        )
        new = ShoppingEntry.objects.create(household=self.home, name="oats", quantity=2)
        self.client.post(f"/shopping/{old.pk}/toggle/")
        new.refresh_from_db()
        self.assertEqual(new.quantity, 3)
        self.assertEqual(ShoppingEntry.objects.count(), 1)


class ShoppingClearTests(ShoppingTests):
    def test_clear_keeps_open_and_foreign_entries(self):
        _, other = kitchen("other")
        ShoppingEntry.objects.create(household=self.home, name="Open")
        ShoppingEntry.objects.create(household=self.home, name="Done", checked=True)
        ShoppingEntry.objects.create(household=other, name="Foreign", checked=True)
        self.client.post("/shopping/clear-checked/")
        self.assertEqual(
            set(ShoppingEntry.objects.values_list("name", flat=True)),
            {"Open", "Foreign"},
        )


class LowStockTests(ShoppingTests):
    def test_multiple_batches_count_towards_one_target(self):
        from pantry.models import Item

        Item.objects.create(household=self.home, name="Rice", quantity=1, unit="kg", low_stock_at=2)
        Item.objects.create(household=self.home, name="rice", quantity=2, unit="kg", low_stock_at=2)
        self.client.post("/shopping/low-stock/")
        self.assertFalse(ShoppingEntry.objects.exists())

    def test_repeated_suggestion_does_not_inflate_list(self):
        from pantry.models import Item

        Item.objects.create(household=self.home, name="Rice", quantity=1, unit="kg", low_stock_at=3)
        self.client.post("/shopping/low-stock/")
        self.client.post("/shopping/low-stock/")
        self.assertEqual(ShoppingEntry.objects.get().quantity, 2)
