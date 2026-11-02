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

class ImportParserTests(TestCase):
    def test_invalid_row_rejects_entire_file(self):
        from pantry.csvio import parse_inventory_csv
        with self.assertRaisesMessage(ValueError,'Line 3'):parse_inventory_csv(b'name,quantity,unit\nRice,1,kg\nBeans,-2,g\n')
    def test_bom_and_optional_columns(self):
        from pantry.csvio import parse_inventory_csv
        rows=parse_inventory_csv('\ufeffname,quantity,unit\nRice,1,kg\n'.encode('utf-8'))
        self.assertEqual(rows[0]['location'],'pantry')
    def test_unknown_and_duplicate_headers_rejected(self):
        from pantry.csvio import parse_inventory_csv
        for data in [b'name,name,quantity,unit\nRice,Rice,1,kg',b'name,quantity,unit,household\nRice,1,kg,9']:
            with self.assertRaises(ValueError):parse_inventory_csv(data)
