from decimal import Decimal
from django.core.exceptions import ValidationError
from django.test import TestCase
from pantry.models import Item
from pantry.tests.factories import kitchen
class InventoryTests(TestCase):
    def setUp(self):
        self.user,self.home=kitchen();self.client.force_login(self.user)
    def test_negative_quantity_rejected(self):
        with self.assertRaises(ValidationError):Item(household=self.home,name='Rice',quantity=-1).full_clean()
    def test_no_date_has_no_urgency(self):
        self.assertIsNone(Item(name='Rice').days_left)

class InventoryAccessTests(TestCase):
    def setUp(self):
        self.user,self.home=kitchen();self.other,self.foreign=kitchen('other');self.client.force_login(self.user)
    def test_cannot_edit_other_household_item(self):
        item=Item.objects.create(household=self.foreign,name='Private rice')
        self.assertEqual(self.client.get(f'/pantry/{item.pk}/edit/').status_code,404)
    def test_foreign_items_not_in_inventory(self):
        Item.objects.create(household=self.foreign,name='Private rice')
        self.assertNotContains(self.client.get('/pantry/'),'Private rice')
    def test_household_is_not_accepted_from_form(self):
        self.client.post('/pantry/new/',{'name':'Rice','category':'grains','location':'pantry','quantity':'2','unit':'kg','household':self.foreign.pk})
        self.assertEqual(Item.objects.get(name='Rice').household,self.home)
