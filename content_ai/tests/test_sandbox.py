from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from content_ai.constants import AIGenerationTask
from content_ai.providers.mock import MOCK_RESPONSE

User = get_user_model()


@override_settings(CONTENT_AI_PROVIDER='mock')
class ContentAISandboxAccessTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('content_ai:sandbox')
        self.user = User.objects.create_user(
            username='sandboxuser',
            password='password123',
        )
        self.superuser = User.objects.create_superuser(
            username='sandboxadmin',
            email='admin@example.com',
            password='password123',
        )

    def test_anonymous_redirects_to_login(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    @override_settings(DEBUG=False)
    def test_regular_user_denied_when_not_debug(self):
        self.client.login(username='sandboxuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 403)

    @override_settings(DEBUG=False)
    def test_superuser_allowed_when_not_debug(self):
        self.client.login(username='sandboxadmin', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Content AI Sandbox')

    @override_settings(DEBUG=True)
    def test_regular_user_allowed_when_debug(self):
        self.client.login(username='sandboxuser', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)


@override_settings(DEBUG=True, CONTENT_AI_PROVIDER='mock')
class ContentAISandboxGenerationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('content_ai:sandbox')
        self.user = User.objects.create_user(
            username='sandboxgen',
            password='password123',
        )
        self.client.login(username='sandboxgen', password='password123')

    def test_successful_generation_with_mock_provider(self):
        response = self.client.post(
            self.url,
            {
                'task': AIGenerationTask.POST_GENERATION,
                'provider': 'mock',
                'title': 'Housing update',
                'source': 'sandbox',
                'language': 'sv',
                'category': 'news',
                'context': 'ctx',
                'instructions': 'short',
                'business_name': '',
                'city': '',
                'description': '',
                'target_audience': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, MOCK_RESPONSE)
        self.assertContains(response, 'mock')
        self.assertContains(response, 'Generation result')
        self.assertContains(response, 'Execution time')

    def test_prompt_preview_is_rendered(self):
        response = self.client.post(
            self.url,
            {
                'task': AIGenerationTask.POST_GENERATION,
                'provider': 'mock',
                'title': 'Unique Sandbox Title',
                'source': 'editorial',
                'language': 'fa',
                'category': 'news',
                'context': 'local',
                'instructions': 'formal',
                'business_name': '',
                'city': '',
                'description': '',
                'target_audience': '',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Prompt preview')
        self.assertContains(response, 'Task: POST_GENERATION')
        self.assertContains(response, 'Title: Unique Sandbox Title')

    def test_ad_generation_with_mock_provider(self):
        response = self.client.post(
            self.url,
            {
                'task': AIGenerationTask.AD_GENERATION,
                'provider': 'mock',
                'title': '',
                'source': '',
                'language': 'sv',
                'category': 'food',
                'context': '',
                'instructions': 'short',
                'business_name': 'Sandbox Cafe',
                'city': 'Stockholm',
                'description': 'Lunch specials',
                'target_audience': 'locals',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Task: AD_GENERATION')
        self.assertContains(response, 'Business name: Sandbox Cafe')
        self.assertContains(response, MOCK_RESPONSE)
