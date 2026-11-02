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
