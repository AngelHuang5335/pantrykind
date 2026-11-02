from django.test import TestCase
from django.contrib.auth.models import User


class AccountTests(TestCase):
    def test_dashboard_requires_login(self):
        self.assertEqual(self.client.get("/app/").status_code, 302)

    def test_signup_and_login(self):
        r = self.client.post(
            "/accounts/signup/",
            {
                "username": "cook",
                "password1": "kitchen-fresh-578!",
                "password2": "kitchen-fresh-578!",
            },
        )
        self.assertEqual(r.status_code, 302)
        self.assertTrue(User.objects.filter(username="cook").exists())

    def test_weak_password_is_rejected(self):
        self.client.post(
            "/accounts/signup/",
            {"username": "cook", "password1": "123", "password2": "123"},
        )
        self.assertEqual(User.objects.count(), 0)

    def test_logout_requires_post(self):
        self.assertEqual(self.client.get("/accounts/logout/").status_code, 405)
