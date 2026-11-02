from django.test import TestCase
from django.utils import timezone
from pantry.models import MealPlan,Recipe,Ingredient,Item,CookLog
from pantry.tests.factories import kitchen
class PlannerTests(TestCase):
    def setUp(self):
        self.user,self.home=kitchen();self.client.force_login(self.user)
        self.recipe=Recipe.objects.create(household=self.home,title='Oats',instructions='Cook',servings=1)
        Ingredient.objects.create(recipe=self.recipe,name='Oats',quantity=1,unit='pcs')
    def test_repeated_cook_is_not_double_deducted(self):
        item=Item.objects.create(household=self.home,name='Oats',quantity=3)
        plan=MealPlan.objects.create(household=self.home,recipe=self.recipe,date=timezone.localdate(),servings=1)
        self.client.post(f'/plan/{plan.pk}/cook/');self.client.post(f'/plan/{plan.pk}/cook/')
        item.refresh_from_db();self.assertEqual(item.quantity,2);self.assertEqual(CookLog.objects.count(),1)
    def test_foreign_recipe_cannot_be_planned(self):
        _,other=kitchen('other');r=Recipe.objects.create(household=other,title='Private',instructions='Cook')
        self.client.post('/plan/',{'recipe':r.pk,'date':timezone.localdate(),'slot':'dinner','servings':2})
        self.assertFalse(MealPlan.objects.exists())
