from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from content_ai.constants import AIGenerationTask
from content_ai.providers.exceptions import GenerationError, ProviderNotFound
from content_ai.providers.mock import MOCK_RESPONSE, MockProvider
from content_ai.services.generation import ContentGenerationService


class ContentGenerationServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = ContentGenerationService()

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_resolves_configured_provider(self):
        with patch(
            'content_ai.services.generation.get_provider',
            wraps=__import__(
                'content_ai.providers.registry',
                fromlist=['get_provider'],
            ).get_provider,
        ) as mocked_get_provider:
            result = self.service.generate(
                AIGenerationTask.POST_GENERATION,
                {'topic': 'test'},
            )
            mocked_get_provider.assert_called_once_with()
        self.assertEqual(result['title'], MOCK_RESPONSE)

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_delegates_post_generation_to_provider(self):
        provider = MagicMock(spec=MockProvider)
        provider.name = 'mock'
        provider.generate_post.return_value = {'title': 'delegated'}

        with patch(
            'content_ai.services.generation.get_provider',
            return_value=provider,
        ):
            result = self.service.generate(
                AIGenerationTask.POST_GENERATION,
                {'topic': 'housing'},
            )

        provider.generate_post.assert_called_once_with(topic='housing')
        self.assertEqual(result, {'title': 'delegated'})

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_delegates_each_supported_task(self):
        cases = (
            (AIGenerationTask.POST_GENERATION, 'generate_post'),
            (AIGenerationTask.AD_GENERATION, 'generate_ad'),
            (AIGenerationTask.REWRITE, 'rewrite'),
            (AIGenerationTask.SUMMARY, 'summarize'),
            (AIGenerationTask.TRANSLATION, 'translate'),
        )
        for task, method_name in cases:
            with self.subTest(task=task):
                provider = MagicMock(spec=MockProvider)
                provider.name = 'mock'
                getattr(provider, method_name).return_value = {'ok': True}
                with patch(
                    'content_ai.services.generation.get_provider',
                    return_value=provider,
                ):
                    result = self.service.generate(task, {})
                getattr(provider, method_name).assert_called_once_with()
                self.assertEqual(result, {'ok': True})

    @override_settings(CONTENT_AI_PROVIDER='openai')
    def test_unknown_provider_raises(self):
        with self.assertRaises(ProviderNotFound):
            self.service.generate(AIGenerationTask.REWRITE, {})

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_mock_response_for_supported_tasks(self):
        post = self.service.generate(AIGenerationTask.POST_GENERATION, {})
        ad = self.service.generate(AIGenerationTask.AD_GENERATION, {})
        rewrite = self.service.generate(AIGenerationTask.REWRITE, {})
        summary = self.service.generate(AIGenerationTask.SUMMARY, {})
        translation = self.service.generate(AIGenerationTask.TRANSLATION, {})

        self.assertEqual(post['content'], MOCK_RESPONSE)
        self.assertEqual(ad['description'], MOCK_RESPONSE)
        self.assertEqual(rewrite['text'], MOCK_RESPONSE)
        self.assertEqual(summary['summary'], MOCK_RESPONSE)
        self.assertEqual(translation['text'], MOCK_RESPONSE)

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_unsupported_task_raises_generation_error(self):
        with self.assertRaises(GenerationError) as ctx:
            self.service.generate(AIGenerationTask.SEO, {})
        self.assertIn('seo', str(ctx.exception).lower())

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_none_payload_treated_as_empty_kwargs(self):
        result = self.service.generate(AIGenerationTask.SUMMARY, None)
        self.assertEqual(result['summary'], MOCK_RESPONSE)
