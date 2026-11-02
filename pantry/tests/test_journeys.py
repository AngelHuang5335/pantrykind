from django.test import TestCase
from django.core.management import call_command
from io import StringIO
from pantry.models import Recipe, Item, StockEvent, ShoppingEntry


class JourneyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command(
            "seed_demo",
            username="demo",
            password="demo-test-only-password-849",
            stdout=StringIO(),
        )

    def setUp(self):
        self.client.login(username="demo", password="demo-test-only-password-849")

    def test_all_primary_pages_render(self):
        recipe = Recipe.objects.first()
        item = Item.objects.first()
        for url in [
            "/",
            "/app/",
            "/pantry/",
            "/pantry/?status=low",
            "/pantry/new/",
            f"/pantry/{item.pk}/",
            f"/pantry/{item.pk}/edit/",
            "/shopping/",
            "/recipes/",
            "/recipes/?ready=1",
            f"/recipes/{recipe.pk}/",
            f"/recipes/{recipe.pk}/?servings=4",
            "/recipes/new/",
            f"/recipes/{recipe.pk}/edit/",
            "/plan/",
            "/plan/calendar.ics",
            "/insights/",
            "/activity/",
            "/households/settings/",
            "/data/import/",
            "/data/pantry.csv",
            "/data/shopping.csv",
            "/api/v1/inventory/",
            "/api/v1/shopping/",
            "/healthz/",
        ]:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 200)

    def test_cook_and_shop_journey(self):
        recipe = Recipe.objects.get(title="Sunshine rice bowl")
        from uuid import uuid4

        self.client.post(f"/recipes/{recipe.pk}/cook/", {"servings": 2, "request_id": str(uuid4())})
        self.assertEqual(StockEvent.objects.count(), 4)
        spinach = Item.objects.get(name="Fresh spinach")
        self.assertEqual(spinach.quantity, 0)
        self.client.post(f"/recipes/{recipe.pk}/shop/", {"servings": 2})
        self.assertTrue(ShoppingEntry.objects.filter(name="Fresh spinach", checked=False).exists())

    def test_seed_does_not_overwrite_an_existing_user(self):
        from django.core.management.base import CommandError

        before = Item.objects.count()
        with self.assertRaises(CommandError):
            call_command("seed_demo", username="demo", noinput=True, stdout=StringIO())
        self.assertEqual(Item.objects.count(), before)
