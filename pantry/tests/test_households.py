from django.contrib.auth.models import User
from django.test import TestCase
from pantry.models import Household, Membership


class HouseholdTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("cook", password="test-pass-1234")
        self.client.force_login(self.user)

    def test_new_user_needs_household(self):
        self.assertRedirects(self.client.get("/app/"), "/households/new/")

    def test_creator_is_owner(self):
        self.client.post("/households/new/", {"name": "Our kitchen"})
        self.assertEqual(Membership.objects.get(user=self.user).role, "owner")
        self.assertEqual(self.client.get("/app/").status_code, 200)

    def test_session_cannot_select_foreign_household(self):
        own = Household.objects.create(name="Own")
        other = Household.objects.create(name="Other")
        Membership.objects.create(household=own, user=self.user, role="owner")
        session = self.client.session
        session["household_id"] = other.pk
        session.save()
        response = self.client.get("/app/")
        self.assertEqual(response.wsgi_request.household, own)


class InvitationTests(TestCase):
    def test_invitation_is_single_use_and_not_consumed_by_preview(self):
        from pantry.tests.factories import kitchen
        from django.contrib.auth.models import User

        owner, home = kitchen()
        self.client.force_login(owner)
        self.client.post("/households/invite/")
        url = self.client.session["pantry_invite_url"]
        guest = User.objects.create_user("guest", password="guest-long-pass-123")
        self.client.force_login(guest)
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertFalse(Membership.objects.filter(user=guest).exists())
        self.client.post(url)
        self.assertTrue(
            Membership.objects.filter(user=guest, household=home, role="member").exists()
        )
        self.assertEqual(self.client.get(url).status_code, 404)

    def test_member_cannot_invite_or_change_settings(self):
        from pantry.tests.factories import kitchen

        owner, home = kitchen()
        guest = User.objects.create_user("guest")
        Membership.objects.create(user=guest, household=home)
        self.client.force_login(guest)
        self.assertEqual(self.client.post("/households/invite/").status_code, 403)
        self.assertEqual(
            self.client.post(
                "/households/settings/",
                {"name": "Hijacked", "timezone_name": "UTC", "reminder_days": 7},
            ).status_code,
            403,
        )
