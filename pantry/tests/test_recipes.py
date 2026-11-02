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
