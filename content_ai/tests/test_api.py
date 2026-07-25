import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from content_ai.providers.exceptions import GenerationError
from content_ai.providers.mock import MOCK_RESPONSE
from content_ai.schemas.responses import GenerationResult
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


@override_settings(CONTENT_AI_PROVIDER='mock')
class InternalEditorialDraftAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('content_ai_api:editorial_draft')
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
                    'source': 'internal',
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
        self.assertEqual(payload['title'], 'API draft')
        self.assertEqual(payload['body'], MOCK_RESPONSE)
        self.assertEqual(payload['summary'], '')
        self.assertEqual(payload['language'], 'sv')
        self.assertIn('metadata', payload)
        self.assertIn('telemetry', payload)
        self.assertIsNotNone(payload['telemetry'])
        self.assertEqual(payload['telemetry']['provider'], 'mock')
        self.assertTrue(payload['telemetry']['success'])
        self.assertIsNotNone(payload['telemetry']['duration_ms'])

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

    def test_get_not_allowed(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 405)
