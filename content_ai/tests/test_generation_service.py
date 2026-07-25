from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from content_ai.constants import AIGenerationTask
from content_ai.providers.exceptions import GenerationError, ProviderNotFound
from content_ai.providers.mock import MOCK_RESPONSE, MockProvider
from content_ai.schemas import (
    AdGenerationRequest,
    GenerationResult,
    PostGenerationRequest,
)
from content_ai.services.generation import ContentGenerationService


class ContentGenerationServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = ContentGenerationService()

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_resolves_configured_provider(self):
        request = PostGenerationRequest(title='test')
        with patch(
            'content_ai.services.generation.get_provider',
            wraps=__import__(
                'content_ai.providers.registry',
                fromlist=['get_provider'],
            ).get_provider,
        ) as mocked_get_provider:
            result = self.service.generate(
                AIGenerationTask.POST_GENERATION,
                request,
            )
            mocked_get_provider.assert_called_once_with(None)
        self.assertIsInstance(result, GenerationResult)
        self.assertEqual(result.content, MOCK_RESPONSE)

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_uses_prompt_registry_and_passes_prompt_string(self):
        request = PostGenerationRequest(title='housing')
        expected = GenerationResult(
            success=True,
            content='delegated',
            provider='mock',
        )
        provider = MagicMock(spec=MockProvider)
        provider.name = 'mock'
        provider.generate_post.return_value = expected

        with patch(
            'content_ai.services.generation.get_provider',
            return_value=provider,
        ):
            result = self.service.generate(
                AIGenerationTask.POST_GENERATION,
                request,
            )

        provider.generate_post.assert_called_once()
        prompt = provider.generate_post.call_args.args[0]
        self.assertIsInstance(prompt, str)
        self.assertIn('Task: POST_GENERATION', prompt)
        self.assertIn('Title: housing', prompt)
        self.assertEqual(result.content, 'delegated')
        self.assertEqual(result.provider, 'mock')
        self.assertIsNotNone(result.telemetry)
        self.assertTrue(result.telemetry.success)

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_ad_generation_passes_prompt_string(self):
        request = AdGenerationRequest(business_name='Cafe')
        provider = MagicMock(spec=MockProvider)
        provider.name = 'mock'
        provider.generate_ad.return_value = GenerationResult(
            success=True,
            content='ad',
            provider='mock',
        )

        with patch(
            'content_ai.services.generation.get_provider',
            return_value=provider,
        ):
            self.service.generate(AIGenerationTask.AD_GENERATION, request)

        prompt = provider.generate_ad.call_args.args[0]
        self.assertIsInstance(prompt, str)
        self.assertIn('Task: AD_GENERATION', prompt)
        self.assertIn('Business name: Cafe', prompt)

    @override_settings(CONTENT_AI_PROVIDER='not-a-provider')
    def test_unknown_provider_raises(self):
        with self.assertRaises(ProviderNotFound):
            self.service.generate(
                AIGenerationTask.POST_GENERATION,
                PostGenerationRequest(),
            )

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_mock_response_is_generation_result_with_prompt_metadata(self):
        request = PostGenerationRequest(title='Hello')
        result = self.service.generate(
            AIGenerationTask.POST_GENERATION,
            request,
        )
        self.assertIsInstance(result, GenerationResult)
        self.assertTrue(result.success)
        self.assertEqual(result.content, MOCK_RESPONSE)
        self.assertEqual(result.provider, 'mock')
        self.assertIn('Title: Hello', result.metadata['prompt'])

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_unsupported_task_raises_generation_error(self):
        with self.assertRaises(GenerationError) as ctx:
            self.service.generate(AIGenerationTask.SEO, None)
        self.assertIn('seo', str(ctx.exception).lower())

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_task_without_prompt_template_raises(self):
        with self.assertRaises(GenerationError) as ctx:
            self.service.generate(AIGenerationTask.REWRITE, None)
        self.assertIn('prompt template', str(ctx.exception).lower())
