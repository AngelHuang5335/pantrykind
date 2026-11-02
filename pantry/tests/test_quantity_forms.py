from django.test import TestCase

from pantry.forms import ShoppingForm
from pantry.models import ShoppingEntry
from pantry.services import add_to_shopping
from pantry.tests.factories import kitchen


class QuantityBoundaryViewTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()
        self.client.force_login(self.user)
        self.large = add_to_shopping(self.home, "Rice", "999999999", "kg")

    def test_form_rejects_an_amount_the_service_would_reject(self):
        form = ShoppingForm({"name": "Rice", "quantity": "999999999.001", "unit": "kg"})
        self.assertFalse(form.is_valid())
        self.assertIn("quantity", form.errors)

    def test_merge_overflow_renders_an_error_instead_of_a_server_failure(self):
        response = self.client.post("/shopping/", {"name": "Rice", "quantity": 1, "unit": "kg"})
        self.assertContains(response, "Shopping quantity is too large")
        self.large.refresh_from_db()
        self.assertEqual(self.large.quantity, 999999999)

    def test_failed_edit_merge_restores_the_original_entry(self):
        other = add_to_shopping(self.home, "Oats", 1, "kg")
        response = self.client.post(
            f"/shopping/{other.pk}/edit/", {"name": "Rice", "quantity": 1, "unit": "kg"}
        )
        self.assertContains(response, "Shopping quantity is too large")
        other.refresh_from_db()
        self.assertEqual(other.name, "Oats")
        self.assertEqual(ShoppingEntry.objects.count(), 2)

    def test_unchecking_an_overflowing_merge_keeps_checked_entry(self):
        checked = ShoppingEntry.objects.create(
            household=self.home, name="Rice", quantity=1, unit="kg", checked=True
        )
        self.assertEqual(self.client.post(f"/shopping/{checked.pk}/toggle/").status_code, 302)
        checked.refresh_from_db()
        self.assertTrue(checked.checked)
