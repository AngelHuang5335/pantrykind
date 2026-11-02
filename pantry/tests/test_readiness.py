from django.test import TestCase, override_settings


class ReadinessTests(TestCase):
    @override_settings(SECURE_SSL_REDIRECT=True, SECURE_REDIRECT_EXEMPT=[r"^healthz/$"])
    def test_loopback_health_probe_does_not_redirect_to_unserved_tls(self):
        self.assertEqual(self.client.get("/healthz/").json(), {"status": "ok"})
        self.assertEqual(self.client.get("/accounts/login/").status_code, 301)
