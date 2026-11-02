from decimal import Decimal

from django.test import RequestFactory, TestCase

from pantry.matching import index_stock, match_recipe
from pantry.models import Ingredient, Item, Recipe
from pantry.tests.factories import kitchen
from pantry.views.recipes import index


class RecipePerformanceTests(TestCase):
    def setUp(self):
        self.user, self.home = kitchen()

    def render(self):
        request = RequestFactory().get("/recipes/")
        request.user, request.household = self.user, self.home
        return index(request)

    def test_catalogue_has_three_queries_at_different_sizes(self):
        for count in (1, 30):
            for number in range(count):
                recipe = Recipe.objects.create(
                    household=self.home, title=f"Meal {count}-{number}", instructions="Cook."
                )
                Ingredient.objects.create(recipe=recipe, name="Rice", quantity=1, unit="kg")
            with self.assertNumQueries(3):
                response = self.render()
                self.assertEqual(response.status_code, 200)
        self.assertLessEqual(response.content.count(b'<article class="card">'), 24)

    def test_shared_index_preserves_matching_and_cannot_be_mutated_by_a_result(self):
        recipe = Recipe.objects.create(household=self.home, title="Rice", instructions="Cook.")
        Ingredient.objects.create(recipe=recipe, name="Rice", quantity=500, unit="g")
        items = [
            Item(household=self.home, name="Rice", quantity=Decimal(".25"), unit="kg"),
            Item(household=self.home, name="rice", quantity=Decimal("300"), unit="g"),
        ]
        stock = index_stock(items)
        expected = match_recipe(recipe, items=items)
        self.assertEqual(match_recipe(recipe, stock_index=stock), expected)
        result = match_recipe(recipe, stock_index=stock)
        result[0]["batches"].clear()
        self.assertEqual(match_recipe(recipe, stock_index=stock), expected)
