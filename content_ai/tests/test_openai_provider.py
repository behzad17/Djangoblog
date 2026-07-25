from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings

from content_ai.providers import (
    GenerationError,
    OpenAIProvider,
    ProviderConfigurationError,
    list_providers,
)
from content_ai.schemas import GenerationResult


class OpenAIProviderRegistryTests(SimpleTestCase):
    def test_openai_is_registered(self):
        self.assertIn('openai', list_providers())

    @override_settings(
        OPENAI_API_KEY='sk-test',
        OPENAI_MODEL='gpt-test',
        OPENAI_TIMEOUT=30,
    )
    def test_get_provider_openai_returns_openai_provider(self):
        client = MagicMock()
        provider = OpenAIProvider(client=client)
        self.assertEqual(provider.name, 'openai')
        self.assertIsInstance(provider, OpenAIProvider)

    def test_list_providers_includes_mock_and_openai(self):
        self.assertEqual(list_providers(), ['mock', 'openai'])


class OpenAIProviderConfigTests(SimpleTestCase):
    @override_settings(OPENAI_API_KEY='', OPENAI_MODEL='gpt-test')
    def test_missing_api_key_raises(self):
        with self.assertRaises(ProviderConfigurationError) as ctx:
            OpenAIProvider(client=MagicMock())
        self.assertIn('OPENAI_API_KEY', str(ctx.exception))

    @override_settings(OPENAI_API_KEY='sk-test', OPENAI_MODEL='')
    def test_missing_model_raises(self):
        with self.assertRaises(ProviderConfigurationError) as ctx:
            OpenAIProvider(client=MagicMock())
        self.assertIn('OPENAI_MODEL', str(ctx.exception))


@override_settings(
    OPENAI_API_KEY='sk-test',
    OPENAI_MODEL='gpt-test-model',
    OPENAI_TIMEOUT=45,
)
class OpenAIProviderGenerationTests(SimpleTestCase):
    def setUp(self):
        self.client = MagicMock()
        self.provider = OpenAIProvider(client=self.client)

    def test_generate_post_success_returns_generation_result(self):
        response = MagicMock()
        response.output_text = 'Generated post body'
        response.id = 'resp_post_1'
        self.client.responses.create.return_value = response

        result = self.provider.generate_post('post prompt')

        self.client.responses.create.assert_called_once_with(
            model='gpt-test-model',
            input='post prompt',
        )
        self.assertIsInstance(result, GenerationResult)
        self.assertTrue(result.success)
        self.assertEqual(result.content, 'Generated post body')
        self.assertEqual(result.provider, 'openai')
        self.assertEqual(result.metadata['task'], 'post_generation')
        self.assertEqual(result.metadata['model'], 'gpt-test-model')
        self.assertEqual(result.metadata['response_id'], 'resp_post_1')
        self.assertIsNotNone(result.telemetry)
        self.assertEqual(result.telemetry.provider, 'openai')
        self.assertEqual(result.telemetry.model, 'gpt-test-model')
        self.assertEqual(result.telemetry.prompt_length, len('post prompt'))
        self.assertEqual(
            result.telemetry.response_length,
            len('Generated post body'),
        )

    def test_generate_ad_success_returns_generation_result(self):
        response = MagicMock()
        response.output_text = 'Generated ad body'
        response.id = 'resp_ad_1'
        self.client.responses.create.return_value = response

        result = self.provider.generate_ad('ad prompt')

        self.client.responses.create.assert_called_once_with(
            model='gpt-test-model',
            input='ad prompt',
        )
        self.assertIsInstance(result, GenerationResult)
        self.assertEqual(result.content, 'Generated ad body')
        self.assertEqual(result.metadata['task'], 'ad_generation')

    def test_sdk_exception_mapped_to_generation_error(self):
        self.client.responses.create.side_effect = RuntimeError('boom')

        with self.assertRaises(GenerationError) as ctx:
            self.provider.generate_post('prompt')

        self.assertIn('OpenAI generation failed', str(ctx.exception))
        self.assertNotIsInstance(ctx.exception, RuntimeError)
        self.assertIsNotNone(ctx.exception.telemetry)
        self.assertFalse(ctx.exception.telemetry.success)
        self.assertEqual(ctx.exception.telemetry.error_type, 'RuntimeError')

    def test_usage_mapped_into_telemetry(self):
        response = MagicMock()
        response.output_text = 'body'
        response.id = 'resp_usage'
        response.usage = MagicMock(
            input_tokens=11,
            output_tokens=7,
            total_tokens=18,
        )
        self.client.responses.create.return_value = response

        result = self.provider.generate_post('prompt')

        self.assertEqual(
            result.telemetry.token_usage,
            {
                'input_tokens': 11,
                'output_tokens': 7,
                'total_tokens': 18,
            },
        )

    def test_missing_output_text_returns_empty_content(self):
        class _Response:
            id = 'resp_empty'

        self.client.responses.create.return_value = _Response()

        result = self.provider.generate_post('prompt')

        self.assertEqual(result.content, '')
        self.assertTrue(result.success)

    def test_uses_responses_api_not_chat_completions(self):
        response = MagicMock()
        response.output_text = 'ok'
        response.id = 'resp_1'
        self.client.responses.create.return_value = response

        self.provider.generate_post('prompt')

        self.client.responses.create.assert_called_once()
        self.client.chat.completions.create.assert_not_called()
