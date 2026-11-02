from django.test import TestCase
from pantry.models import Item
from pantry.tests.factories import kitchen
class ExportTests(TestCase):
    def test_export_scopes_household_and_escapes_formulas(self):
        user,home=kitchen();_,other=kitchen('other');self.client.force_login(user)
        Item.objects.create(household=home,name='=SUM(A1:A2)')
        Item.objects.create(household=other,name='Private food')
        response=self.client.get('/data/pantry.csv');text=response.content.decode('utf-8-sig')
        self.assertIn("'=SUM(A1:A2)",text);self.assertNotIn('Private food',text)
