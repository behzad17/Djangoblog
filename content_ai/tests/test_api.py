import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from content_ai.providers.exceptions import GenerationError
from content_ai.providers.mock import MOCK_RESPONSE
from content_ai.telemetry import AIExecutionTelemetry

User = get_user_model()


@override_settings(CONTENT_AI_PROVIDER='mock')
class InternalEditorialDraftAPIAuthTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('content_ai_api:editorial_draft')
        self.user = User.objects.create_user(
            username='apiuser',
            password='password123',
        )
        self.staff = User.objects.create_user(
            username='apistaff',
            password='password123',
            is_staff=True,
        )
        self.superuser = User.objects.create_superuser(
            username='apisuper',
            email='super@example.com',
            password='password123',
        )

    def test_anonymous_returns_401(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'title': 'T'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()['error']['code'], 'unauthorized')

    def test_non_staff_returns_403(self):
        self.client.login(username='apiuser', password='password123')
        response = self.client.post(
            self.url,
            data=json.dumps({'title': 'T'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()['error']['code'], 'forbidden')

    def test_superuser_allowed(self):
        self.client.login(username='apisuper', password='password123')
        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    'title': 'Super draft',
                    'language': 'sv',
                    'category': 'news',
                    'context': 'ctx',
                    'instructions': 'short',
                    'provider_name': 'mock',
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)


@override_settings(CONTENT_AI_PROVIDER='mock')
class InternalEditorialDraftAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('content_ai_api:editorial_draft')
        self.assertEqual(self.url, '/api/internal/ai/editorial/draft/')
        self.staff = User.objects.create_user(
            username='draftstaff',
            password='password123',
            is_staff=True,
        )
        self.client.login(username='draftstaff', password='password123')

    def test_successful_generation_returns_draft_schema(self):
        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    'title': 'API draft',
                    'language': 'sv',
                    'category': 'news',
                    'context': 'ctx',
                    'instructions': 'short',
                    'provider_name': 'mock',
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        # Mock provider returns unlabelled text; two-pass uses it as title/lead/body.
        self.assertEqual(payload['title'], MOCK_RESPONSE)
        self.assertEqual(payload['lead'], MOCK_RESPONSE)
        self.assertEqual(payload['body'], MOCK_RESPONSE)
        self.assertEqual(payload['summary'], MOCK_RESPONSE)
        self.assertEqual(payload['language'], 'sv')
        self.assertIn('metadata', payload)
        self.assertEqual(
            payload['metadata'].get('generation_passes'),
            ['headline_lead', 'body'],
        )
        self.assertIn('telemetry', payload)
        self.assertIsNotNone(payload['telemetry'])
        self.assertEqual(payload['telemetry']['provider'], 'mock')
        self.assertTrue(payload['telemetry']['success'])
        self.assertIsNotNone(payload['telemetry']['duration_ms'])

    def test_response_does_not_expose_prompt_strings(self):
        response = self.client.post(
            self.url,
            data=json.dumps(
                {
                    'title': 'Secret prompt check',
                    'language': 'sv',
                    'category': 'news',
                    'context': 'ctx',
                    'instructions': 'short',
                    'provider_name': 'mock',
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertNotIn('prompt', payload.get('metadata', {}))
        raw = json.dumps(payload)
        self.assertNotIn('Task: POST_GENERATION', raw)
        self.assertNotIn('System: You are a Peyvand', raw)

    def test_invalid_json_returns_400(self):
        response = self.client.post(
            self.url,
            data='{not-json',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'invalid_json')

    def test_unknown_field_returns_400(self):
        response = self.client.post(
            self.url,
            data=json.dumps({'title': 'T', 'unexpected': 'x'}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'validation_error')

    def test_provider_failure_returns_502_without_sdk_leak(self):
        with patch(
            'content_ai.api.EditorialAIService.generate_draft',
            side_effect=GenerationError(
                'generation failed',
                telemetry=AIExecutionTelemetry(
                    provider='mock',
                    success=False,
                    error_type='GenerationError',
                    duration_ms=1.5,
                ),
            ),
        ):
            response = self.client.post(
                self.url,
                data=json.dumps({'title': 'T', 'provider_name': 'mock'}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 502)
        payload = response.json()
        self.assertEqual(payload['error']['code'], 'generation_failed')
        self.assertNotIn('Traceback', payload['error']['message'])
        self.assertEqual(payload['telemetry']['success'], False)
        self.assertEqual(payload['telemetry']['error_type'], 'GenerationError')

    def test_unexpected_failure_returns_500(self):
        with patch(
            'content_ai.api.EditorialAIService.generate_draft',
            side_effect=RuntimeError('boom'),
        ):
            response = self.client.post(
                self.url,
                data=json.dumps({'title': 'T', 'provider_name': 'mock'}),
                content_type='application/json',
            )
        self.assertEqual(response.status_code, 500)
        payload = response.json()
        self.assertEqual(payload['error']['code'], 'internal_error')
        self.assertNotIn('boom', payload['error']['message'])

    def test_get_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)

    def test_legacy_path_still_works(self):
        legacy_url = reverse('content_ai_editorial_draft_legacy')
        self.assertEqual(legacy_url, '/api/internal/content-ai/editorial/draft/')
        response = self.client.post(
            legacy_url,
            data=json.dumps(
                {
                    'title': 'Legacy',
                    'language': 'sv',
                    'provider_name': 'mock',
                }
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['title'], MOCK_RESPONSE)
