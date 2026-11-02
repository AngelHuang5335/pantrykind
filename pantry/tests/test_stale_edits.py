from uuid import uuid4

from django.test import TestCase

from pantry.models import Item
from pantry.services import record_stock
from pantry.tests.factories import kitchen


class StaleEditTests(TestCase):
    def test_consumption_invalidates_an_already_open_edit_form(self):
        user, home = kitchen()
        self.client.force_login(user)
        item = Item.objects.create(household=home, name="Rice", quantity=2, unit="kg")
        revision = item.updated_at.isoformat()
        record_stock(
            household=home, item_id=item.pk, actor=user, kind="used", amount=1, request_id=uuid4()
        )
        response = self.client.post(
            f"/pantry/{item.pk}/edit/",
            {
                "revision": revision,
                "name": "Stale name",
                "category": "grains",
                "location": "pantry",
                "unit": "kg",
                "low_stock_at": 0,
            },
        )
        self.assertContains(response, "changed while you were editing")
        item.refresh_from_db()
        self.assertEqual(item.quantity, 1)
        self.assertEqual(item.name, "Rice")

    def test_current_revision_can_update_metadata(self):
        user, home = kitchen()
        self.client.force_login(user)
        item = Item.objects.create(household=home, name="Rice", quantity=2, unit="kg")
        response = self.client.post(
            f"/pantry/{item.pk}/edit/",
            {
                "revision": item.updated_at.isoformat(),
                "name": "Brown rice",
                "category": "grains",
                "location": "pantry",
                "unit": "kg",
                "low_stock_at": 0,
            },
        )
        self.assertEqual(response.status_code, 302)
        item.refresh_from_db()
        self.assertEqual(item.name, "Brown rice")
