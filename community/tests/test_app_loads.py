from django.apps import apps
from django.test import Client, SimpleTestCase, TestCase
from django.urls import reverse


class CommunityAppConfigTests(SimpleTestCase):
    def test_app_is_installed(self):
        config = apps.get_app_config('community')
        self.assertEqual(config.name, 'community')
        self.assertEqual(config.verbose_name, 'Community')


class CommunityHealthEndpointTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_health_endpoint_returns_ok(self):
        response = self.client.get(reverse('community:health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'app': 'community'})
