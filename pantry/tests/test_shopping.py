from django.test import TestCase
from pantry.tests.factories import kitchen
from pantry.models import ShoppingEntry
class ShoppingTests(TestCase):
    def setUp(self):self.user,self.home=kitchen();self.client.force_login(self.user)
    def test_add_entry(self):
        self.client.post('/shopping/',{'name':'Oats','quantity':'2','unit':'pack'})
        self.assertEqual(ShoppingEntry.objects.get().household,self.home)
    def test_foreign_entries_are_private(self):
        user,other=kitchen('other');ShoppingEntry.objects.create(household=other,name='Private oats')
        self.assertNotContains(self.client.get('/shopping/'),'Private oats')

class ShoppingMergeTests(ShoppingTests):
    def test_case_and_whitespace_merge(self):
        self.client.post('/shopping/',{'name':'Oats','quantity':1,'unit':'pack'})
        self.client.post('/shopping/',{'name':'  OATS  ','quantity':2,'unit':'pack'})
        self.assertEqual(ShoppingEntry.objects.count(),1);self.assertEqual(ShoppingEntry.objects.get().quantity,3)
    def test_incompatible_units_do_not_merge(self):
        self.client.post('/shopping/',{'name':'Oats','quantity':1,'unit':'pack'})
        self.client.post('/shopping/',{'name':'Oats','quantity':2,'unit':'g'})
        self.assertEqual(ShoppingEntry.objects.count(),2)
