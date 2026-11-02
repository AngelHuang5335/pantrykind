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

class ImportViewTests(TestCase):
    def test_confirmation_is_required_and_replay_does_not_duplicate(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        user,home=kitchen();self.client.force_login(user)
        self.client.post('/data/import/',{'file':SimpleUploadedFile('food.csv',b'name,quantity,unit\nRice,2,kg\n')})
        self.assertFalse(Item.objects.exists())
        token=self.client.session['pantry_import']['token']
        self.client.post('/data/import/confirm/',{'token':token});self.client.post('/data/import/confirm/',{'token':token})
        self.assertEqual(Item.objects.count(),1)
    def test_switching_household_invalidates_preview(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        user,home=kitchen();self.client.force_login(user)
        self.client.post('/data/import/',{'file':SimpleUploadedFile('food.csv',b'name,quantity,unit\nRice,2,kg\n')})
        pending=self.client.session['pantry_import'];pending['household_id']=999
        session=self.client.session;session['pantry_import']=pending;session.save()
        self.client.post('/data/import/confirm/',{'token':pending['token']});self.assertFalse(Item.objects.exists())

class ImportReceiptTests(TestCase):
    def test_stale_concurrent_session_cannot_reimport_same_preview(self):
        from django.core.files.uploadedfile import SimpleUploadedFile
        user,home=kitchen();self.client.force_login(user)
        self.client.post('/data/import/',{'file':SimpleUploadedFile('food.csv',b'name,quantity,unit\nRice,2,kg\n')})
        pending=self.client.session['pantry_import']
        self.client.post('/data/import/confirm/',{'token':pending['token']})
        session=self.client.session;session['pantry_import']=pending;session.save()
        self.client.post('/data/import/confirm/',{'token':pending['token']})
        self.assertEqual(Item.objects.count(),1)
