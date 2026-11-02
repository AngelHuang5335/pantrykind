from django.test import TestCase, Client
from pantry.tests.factories import kitchen
from pantry.models import Item, ShoppingEntry


class SecurityTests(TestCase):
    def test_mutations_need_csrf(self):
        user, home = kitchen()
        client = Client(enforce_csrf_checks=True)
        client.force_login(user)
        self.assertEqual(client.post("/pantry/new/", {"name": "Injected"}).status_code, 403)

    def test_authenticated_pages_are_not_cacheable(self):
        user, home = kitchen()
        self.client.force_login(user)
        r = self.client.get("/app/")
        self.assertEqual(r["Cache-Control"], "private, no-store")
        self.assertIn("script-src 'self'", r["Content-Security-Policy"])

    def test_get_cannot_change_shopping(self):
        user, home = kitchen()
        self.client.force_login(user)
        item = ShoppingEntry.objects.create(household=home, name="Rice")
        self.assertEqual(self.client.get(f"/shopping/{item.pk}/toggle/").status_code, 405)
        item.refresh_from_db()
        self.assertFalse(item.checked)

    def test_food_names_are_escaped(self):
        user, home = kitchen()
        self.client.force_login(user)
        Item.objects.create(household=home, name="<script>alert(1)</script>")
        r = self.client.get("/pantry/")
        self.assertNotContains(r, "<script>alert(1)</script>")
        self.assertContains(r, "&lt;script&gt;")

    def test_api_requires_authentication_and_household_scope(self):
        self.assertEqual(self.client.get("/api/v1/inventory/").status_code, 302)
        user, home = kitchen()
        _, other = kitchen("other")
        Item.objects.create(household=other, name="Private")
        self.client.force_login(user)
        self.assertEqual(self.client.get("/api/v1/inventory/").json()["items"], [])
