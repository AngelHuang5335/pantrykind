"""Explicit opt-in real-browser suite: manage.py test browser_tests.

The normal unit suite does not launch browsers. CI enables this suite separately.
"""

import os
from datetime import timedelta
from pathlib import Path
from unittest import SkipTest

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils import timezone

from pantry.models import Ingredient, Item, Notification, PurchaseReceipt, Recipe, ShoppingEntry
from pantry.reminders import enqueue_reminders
from pantry.services import add_to_shopping
from pantry.tests.factories import kitchen
from pantry.worker import process_one


class KitchenBrowserTests(StaticLiveServerTestCase):
    @classmethod
    def setUpClass(cls):
        if os.environ.get("PANTRY_E2E") != "1":
            raise SkipTest(
                "Browser suite requires explicit PANTRY_E2E=1 and requirements-browser.txt"
            )
        super().setUpClass()
        from playwright.sync_api import sync_playwright

        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        cls.browser = cls.playwright.chromium.launch()
        cls.addClassCleanup(cls.browser.close)

    def setUp(self):
        self.user, self.home = kitchen("browser-cook")
        self.entry = add_to_shopping(self.home, "Rice", 3, "kg")
        self.recipe = Recipe.objects.create(
            household=self.home, title="Rice bowl", instructions="Cook."
        )
        Ingredient.objects.create(recipe=self.recipe, name="Rice", quantity=250, unit="g")
        self.context = self.browser.new_context(viewport={"width": 390, "height": 844})
        self.context.tracing.start(screenshots=True, snapshots=True, sources=True)
        self.page = self.context.new_page()
        self.page.goto(self.live_server_url + "/accounts/login/")
        self.page.get_by_label("Username").fill("browser-cook")
        self.page.get_by_label("Password").fill("kitchen-test-pass-234")
        self.page.get_by_role("button", name="Sign in", exact=True).click()
        self.page.wait_for_url("**/app/")

    def tearDown(self):
        artifacts = Path("test-results")
        artifacts.mkdir(exist_ok=True)
        try:
            self.page.screenshot(
                path=str(artifacts / f"{self._testMethodName}.png"), full_page=True
            )
            self.context.tracing.stop(path=str(artifacts / f"{self._testMethodName}.zip"))
        finally:
            self.context.close()
            super().tearDown()

    def test_partial_purchase_replay_and_cooking_journey(self):
        from playwright.sync_api import expect

        self.page.get_by_role("link", name="Shopping", exact=True).click()
        self.page.get_by_role("link", name="Put away", exact=True).click()
        self.page.get_by_label("Quantity bought").fill("1")
        self.page.get_by_label("Date on the label").fill(
            (timezone.localdate() + timedelta(days=1)).isoformat()
        )
        payload = self.page.locator("form.purchase-form").evaluate(
            "form => Object.fromEntries(new FormData(form))"
        )
        purchase_url = self.page.url
        self.page.get_by_role("button", name="Save purchase & add to pantry", exact=True).click()
        expect(self.page.get_by_role("heading", name="Rice", exact=True)).to_be_visible()
        status = self.page.evaluate(
            """async ({url, payload}) => {
            const response = await fetch(url, {method:'POST', body:new URLSearchParams(payload)});
            return response.status;
        }""",
            {"url": purchase_url, "payload": payload},
        )
        self.assertEqual(status, 200)
        self.assertEqual(PurchaseReceipt.objects.count(), 1)
        self.assertEqual(ShoppingEntry.objects.get(pk=self.entry.pk).quantity, 2)
        self.page.goto(self.live_server_url + f"/recipes/{self.recipe.pk}/")
        self.page.get_by_role("button", name="I cooked this", exact=False).click()
        expect(
            self.page.get_by_text("Meal recorded. Your pantry has been updated.", exact=True)
        ).to_be_visible()
        self.assertEqual(Item.objects.get(name="Rice").quantity, 0.750)

    def test_preferences_delivery_and_mark_read(self):
        from playwright.sync_api import expect

        Item.objects.create(
            household=self.home,
            name="Fresh oats",
            quantity=1,
            expiry_date=timezone.localdate() + timedelta(days=1),
        )
        self.page.get_by_role("link", name="Inbox", exact=True).click()
        self.page.get_by_label("Remind me in my inbox").check()
        self.page.get_by_label("Hour of the day").fill("0")
        self.page.get_by_role("button", name="Save preferences").click()
        expect(
            self.page.get_by_text("Your reminder preferences are saved.", exact=True)
        ).to_be_visible()
        self.assertEqual(enqueue_reminders(), 1)
        self.assertEqual(process_one(), "sent")
        self.page.reload()
        expect(self.page.get_by_text("Fresh oats", exact=True)).to_be_visible()
        self.page.get_by_role("button", name="Mark as read", exact=True).click()
        self.assertIsNotNone(Notification.objects.get().read_at)

    def test_primary_mobile_pages_have_no_horizontal_overflow(self):
        for path in (
            "/app/",
            "/pantry/",
            "/shopping/",
            f"/shopping/{self.entry.pk}/purchase/",
            "/shopping/purchases/",
            "/recipes/",
            "/inbox/",
            "/plan/",
        ):
            self.page.goto(self.live_server_url + path)
            self.assertFalse(
                self.page.evaluate("document.documentElement.scrollWidth > innerWidth"), path
            )
            self.assertEqual(self.page.locator("main").count(), 1)
