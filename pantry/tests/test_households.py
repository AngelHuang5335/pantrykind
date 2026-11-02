from django.contrib.auth.models import User
from django.test import TestCase
from pantry.models import Household,Membership
class HouseholdTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user('cook',password='test-pass-1234')
        self.client.force_login(self.user)
    def test_new_user_needs_household(self):
        self.assertRedirects(self.client.get('/app/'),'/households/new/')
    def test_creator_is_owner(self):
        self.client.post('/households/new/',{'name':'Our kitchen'})
        self.assertEqual(Membership.objects.get(user=self.user).role,'owner')
        self.assertEqual(self.client.get('/app/').status_code,200)
    def test_session_cannot_select_foreign_household(self):
        own=Household.objects.create(name='Own');other=Household.objects.create(name='Other')
        Membership.objects.create(household=own,user=self.user,role='owner')
        session=self.client.session;session['household_id']=other.pk;session.save()
        response=self.client.get('/app/')
        self.assertEqual(response.wsgi_request.household,own)
