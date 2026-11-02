from uuid import uuid4

from django.test import Client, TestCase

from pantry.models import Item, PurchaseReceipt
from pantry.services import add_to_shopping
from pantry.tests.factories import kitchen


class PurchaseViewTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.client.force_login(self.user)
        self.entry = add_to_shopping(self.home, "Oats", 3, "pack")
        self.url = f"/shopping/{self.entry.pk}/purchase/"
        self.data = {
            "amount": 1,
            "request_id": str(uuid4()),
            "category": "grains",
            "location": "pantry",
            "expiry_date": "2030-01-01",
        }

    def test_get_does_not_receive_stock(self):
        self.assertContains(self.client.get(self.url), "Quantity bought")
        self.assertFalse(Item.objects.exists())

    def test_replayed_post_does_not_create_second_batch(self):
        first = self.client.post(self.url, self.data)
        self.assertEqual(first.status_code, 302)
        second = self.client.post(self.url, self.data)
        self.assertEqual(second.url, first.url)
        self.assertEqual(PurchaseReceipt.objects.count(), 1)
        self.assertContains(self.client.get("/shopping/purchases/"), "Oats")

    def test_browser_retry_after_clearing_list_returns_original_purchase(self):
        data = self.data | {"amount": 3}
        first = self.client.post(self.url, data)
        self.client.post("/shopping/clear-checked/")
        retry = self.client.post(self.url, data)
        self.assertEqual(retry.status_code, 302)
        self.assertEqual(retry.url, first.url)
        self.assertEqual(PurchaseReceipt.objects.count(), 1)

    def test_cross_household_purchase_is_not_found(self):
        _, home = kitchen("other")
        foreign = add_to_shopping(home, "Private food", 1, "pack")
        self.assertEqual(
            self.client.post(f"/shopping/{foreign.pk}/purchase/", self.data).status_code, 404
        )

    def test_purchase_requires_csrf(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(self.url, self.data).status_code, 403)
