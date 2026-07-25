from django.apps import apps
from django.test import SimpleTestCase


class ContentAiAppConfigTests(SimpleTestCase):
    def test_app_is_installed(self):
        config = apps.get_app_config('content_ai')
        self.assertEqual(config.name, 'content_ai')
        self.assertEqual(config.verbose_name, 'Content AI')
