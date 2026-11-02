from decimal import Decimal
from django.test import TestCase
from pantry.tests.factories import kitchen
from pantry.models import Recipe,Ingredient,Item
from pantry.matching import match_recipe
class RecipeMatchTests(TestCase):
    def setUp(self):
        self.user,self.home=kitchen();self.recipe=Recipe.objects.create(household=self.home,title='Rice bowl',instructions='Cook.',servings=2)
        Ingredient.objects.create(recipe=self.recipe,name='Rice',quantity=250,unit='g')
    def test_convert_kg_to_g(self):
        Item.objects.create(household=self.home,name=' rice ',quantity=Decimal('.5'),unit='kg')
        result=match_recipe(self.recipe)[0];self.assertTrue(result['ready']);self.assertEqual(result['available'],500)
    def test_different_unit_is_not_assumed(self):
        Item.objects.create(household=self.home,name='Rice',quantity=3,unit='pack')
        self.assertEqual(match_recipe(self.recipe)[0]['missing'],250)
    def test_scaling_changes_required_quantity(self):
        self.assertEqual(match_recipe(self.recipe,4)[0]['needed'],500)
    def test_foreign_stock_does_not_match(self):
        _,other=kitchen('other');Item.objects.create(household=other,name='Rice',quantity=2,unit='kg')
        self.assertEqual(match_recipe(self.recipe)[0]['available'],0)

class RecipeCookingTests(RecipeMatchTests):
    def test_cooking_deducts_oldest_batch_first(self):
        from datetime import timedelta
        from django.utils import timezone
        from pantry.services import cook_recipe
        from uuid import uuid4
        old=Item.objects.create(household=self.home,name='Rice',quantity=100,unit='g',expiry_date=timezone.localdate()+timedelta(days=1))
        fresh=Item.objects.create(household=self.home,name='Rice',quantity=300,unit='g',expiry_date=timezone.localdate()+timedelta(days=10))
        cook_recipe(household=self.home,recipe_id=self.recipe.pk,actor=self.user,servings=2,request_id=uuid4())
        old.refresh_from_db();fresh.refresh_from_db();self.assertEqual(old.quantity,0);self.assertEqual(fresh.quantity,150)
    def test_missing_ingredient_cannot_partially_deduct_stock(self):
        from pantry.services import cook_recipe
        from django.core.exceptions import ValidationError
        from uuid import uuid4
        item=Item.objects.create(household=self.home,name='Rice',quantity=1,unit='kg')
        Ingredient.objects.create(recipe=self.recipe,name='Beans',quantity=1,unit='pack')
        with self.assertRaises(ValidationError):cook_recipe(household=self.home,recipe_id=self.recipe.pk,actor=self.user,servings=2,request_id=uuid4())
        item.refresh_from_db();self.assertEqual(item.quantity,1)
