"""Tests for AI Studio (APF-002)."""

from __future__ import annotations

import json

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from content_ai.config.ai_engine import ENABLE_AI_STUDIO, FEATURE_FLAGS
from content_ai.studio.modules import list_modules_for_ui
from content_ai.studio.services import StudioService

User = get_user_model()


class StudioFlagTests(SimpleTestCase):
    def test_studio_flag_enabled(self):
        self.assertTrue(ENABLE_AI_STUDIO)
        self.assertTrue(FEATURE_FLAGS['ENABLE_AI_STUDIO'])


class StudioModuleCatalogueTests(SimpleTestCase):
    def test_core_modules_present(self):
        ids = {m['id'] for m in list_modules_for_ui()}
        self.assertIn('prompt_lab', ids)
        self.assertIn('knowledge_lab', ids)
        self.assertIn('provider_lab', ids)
        self.assertIn('evaluation_lab', ids)
        self.assertIn('workflow_inspector', ids)
        self.assertIn('generation_history', ids)
        self.assertIn('system_health', ids)
        future = next(m for m in list_modules_for_ui() if m['id'] == 'future_labs')
        self.assertEqual(future['status'], 'future')


class StudioServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = StudioService()
        self.session = self.service.new_session(environment='testing')

    def test_environment_rejects_production(self):
        with self.assertRaises(ValueError):
            self.session.set_environment('production')

    def test_prompt_preview_and_compare(self):
        preview = self.service.preview_prompt(
            self.session,
            version='v1',
            style='news',
            user_prompt='Test housing article',
        )
        self.assertIn('assembled_prompt', preview)
        self.assertIn('components', preview)
        self.assertGreater(preview['estimated_token_usage'], 0)

        compared = self.service.compare_prompts(
            self.session,
            version_a='v1',
            style_a='news',
            version_b='v1',
            style_b='analysis',
            user_prompt='Test',
        )
        self.assertIsNone(compared['automatic_winner'])
        self.assertIn('a', compared)
        self.assertIn('b', compared)

    def test_knowledge_browse_and_compare(self):
        browse = self.service.browse_knowledge(self.session)
        self.assertGreaterEqual(browse['module_count'], 1)
        self.assertFalse(browse['rag_ready'])

        compared = self.service.compare_knowledge(self.session)
        self.assertIsNone(compared['automatic_winner'])
        self.assertEqual(compared['dimension'], 'knowledge')

    def test_provider_inspect(self):
        payload = self.service.inspect_providers(self.session)
        names = {p['name'] for p in payload['providers']}
        self.assertIn('mock', names)

    def test_evaluate_integration(self):
        result = self.service.evaluate_text(
            self.session,
            output_text='A readable body with enough structure for metrics.',
            input_text='source',
            prompt_version='v1',
        )
        self.assertIn('overall', result)
        self.assertIn('scores', result)

    def test_workflow_inspect(self):
        result = self.service.inspect_workflow(
            self.session,
            state='drafting',
        )
        self.assertEqual(result['current_stage'], 'drafting')
        self.assertIn('transitions_map', result)
        self.assertFalse(result['can_examples']['to_published'])

    def test_run_test_and_history_compare(self):
        first = self.service.run_test_generation(
            self.session,
            user_prompt='First studio test',
            provider_name='mock',
        )
        second = self.service.run_test_generation(
            self.session,
            user_prompt='Second studio test',
            provider_name='mock',
            style='analysis',
        )
        history = self.service.generation_history(self.session)
        self.assertEqual(history['count'], 2)
        self.assertFalse(self.session.to_dict()['writes_production'])
        self.assertFalse(self.session.to_dict()['auto_publish_allowed'])

        compared = self.service.compare_generations(
            self.session,
            generation_id_a=first['generation_id'],
            generation_id_b=second['generation_id'],
        )
        self.assertIsNone(compared['automatic_winner'])
        self.assertIn('evaluation', compared)

    def test_system_health(self):
        health = self.service.system_health(self.session)
        self.assertFalse(health['writes_production'])
        self.assertIn('ENABLE_AI_STUDIO', health['feature_flags'])


@override_settings(CONTENT_AI_PROVIDER='mock')
class StudioPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('content_ai:ai_studio')
        self.api = reverse('content_ai:studio_api', kwargs={'action': 'reset'})
        self.user = User.objects.create_user(
            username='studio_user', password='password123'
        )
        self.staff = User.objects.create_user(
            username='studio_staff', password='password123', is_staff=True
        )

    def test_anonymous_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_non_staff_forbidden(self):
        self.client.login(username='studio_user', password='password123')
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (302, 403))

    def test_staff_can_open_studio(self):
        self.client.login(username='studio_staff', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Studio')

    def test_api_requires_staff(self):
        response = self.client.post(
            self.api,
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)


@override_settings(CONTENT_AI_PROVIDER='mock')
class StudioAPIIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(
            username='studio_api_staff',
            password='password123',
            is_staff=True,
        )
        self.client.login(username='studio_api_staff', password='password123')

    def _post(self, action, payload=None):
        url = reverse('content_ai:studio_api', kwargs={'action': action})
        return self.client.post(
            url,
            data=json.dumps(payload or {}),
            content_type='application/json',
        )

    def test_prompt_compare_api(self):
        response = self._post(
            'prompt_compare',
            {
                'version_a': 'v1',
                'style_a': 'news',
                'version_b': 'v1',
                'style_b': 'friendly',
                'user_prompt': 'API compare',
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertIsNone(data['result']['automatic_winner'])

    def test_knowledge_and_provider_api(self):
        kb = self._post('knowledge_browse', {})
        self.assertEqual(kb.status_code, 200)
        self.assertGreaterEqual(kb.json()['result']['module_count'], 1)

        providers = self._post('provider_inspect', {})
        self.assertEqual(providers.status_code, 200)
        names = {p['name'] for p in providers.json()['result']['providers']}
        self.assertIn('mock', names)

    def test_evaluate_and_workflow_api(self):
        ev = self._post(
            'evaluate',
            {'output_text': 'Enough text for evaluation heuristics to run.'},
        )
        self.assertEqual(ev.status_code, 200)
        self.assertIn('overall', ev.json()['result'])

        wf = self._post('workflow_inspect', {'state': 'reviewing'})
        self.assertEqual(wf.status_code, 200)
        self.assertEqual(wf.json()['result']['current_stage'], 'reviewing')

    def test_run_test_history_and_compare(self):
        a = self._post(
            'run_test',
            {'user_prompt': 'Gen A', 'provider': 'mock'},
        )
        b = self._post(
            'run_test',
            {'user_prompt': 'Gen B', 'provider': 'mock'},
        )
        self.assertEqual(a.status_code, 200)
        self.assertEqual(b.status_code, 200)
        id_a = a.json()['result']['generation_id']
        id_b = b.json()['result']['generation_id']

        history = self._post('history', {})
        self.assertEqual(history.status_code, 200)
        self.assertEqual(history.json()['result']['count'], 2)

        compared = self._post(
            'compare_generations',
            {'generation_id_a': id_a, 'generation_id_b': id_b},
        )
        self.assertEqual(compared.status_code, 200)
        self.assertIsNone(compared.json()['result']['automatic_winner'])
        self.assertFalse(compared.json()['session']['writes_production'])

    def test_set_environment_rejects_production(self):
        response = self._post('set_environment', {'environment': 'production'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'validation_error')

    def test_system_health_api(self):
        response = self._post('system_health', {})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['result']['auto_publish_allowed'])
