from decimal import Decimal
from uuid import uuid4

from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase

from pantry.models import CookLog, Ingredient, Item, Membership, Recipe, StockEvent
from pantry.services import add_to_shopping, cook_recipe, record_stock
from pantry.tests.factories import kitchen


class ConsistencyTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.item = Item.objects.create(household=self.home, name="Rice", quantity=1, unit="kg")

    def movement(self, **overrides):
        data = dict(
            household=self.home,
            item_id=self.item.pk,
            actor=self.user,
            kind="used",
            amount=1,
            request_id=uuid4(),
        )
        return record_stock(**(data | overrides))

    def test_retry_after_archiving_returns_original_receipt(self):
        key = uuid4()
        original = self.movement(request_id=key)
        self.item.archived = True
        self.item.save()
        self.assertEqual(self.movement(request_id=key), original)
        self.assertEqual(StockEvent.objects.count(), 1)

    def test_retry_cannot_change_audit_reason(self):
        key = uuid4()
        self.movement(request_id=key, note="Lunch")
        with self.assertRaises(ValidationError):
            self.movement(request_id=key, note="Dinner")

    def test_restock_overflow_rolls_back(self):
        with self.assertRaises(ValidationError):
            self.movement(kind="restocked", amount=Decimal("999999999"))
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 1)
        self.assertFalse(StockEvent.objects.exists())

    def test_revoked_member_cannot_use_stale_household_reference(self):
        Membership.objects.filter(user=self.user).delete()
        with self.assertRaises(PermissionDenied):
            self.movement()

    def test_shopping_service_rejects_invalid_values_without_form(self):
        for value in ["garbage", "NaN", ".0001", "1000000000"]:
            with self.assertRaises(ValidationError):
                add_to_shopping(self.home, "Rice", value, "kg")

    def test_cooking_replay_succeeds_even_after_all_stock_is_used(self):
        recipe = Recipe.objects.create(household=self.home, title="Rice", instructions="Cook.")
        Ingredient.objects.create(recipe=recipe, name="Rice", quantity=1, unit="kg")
        data = dict(
            household=self.home,
            recipe_id=recipe.pk,
            actor=self.user,
            servings=recipe.servings,
            request_id=uuid4(),
        )
        first = cook_recipe(**data)
        self.assertEqual(cook_recipe(**data), first)
        self.assertEqual(CookLog.objects.count(), 1)
        self.item.refresh_from_db()
        self.assertEqual(self.item.quantity, 0)
