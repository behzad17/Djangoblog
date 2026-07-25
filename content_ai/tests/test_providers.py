from django.test import SimpleTestCase, override_settings

from content_ai.providers import (
    BaseAIProvider,
    GenerationError,
    MockProvider,
    ProviderConfigurationError,
    ProviderNotFound,
    get_provider,
    list_providers,
)
from content_ai.providers.mock import MOCK_RESPONSE


class ProviderRegistryTests(SimpleTestCase):
    def test_list_providers_includes_mock(self):
        self.assertEqual(list_providers(), ['mock'])

    @override_settings(CONTENT_AI_PROVIDER='mock')
    def test_get_provider_uses_settings_when_name_omitted(self):
        provider = get_provider()
        self.assertIsInstance(provider, MockProvider)
        self.assertEqual(provider.name, 'mock')

    def test_get_provider_by_name(self):
        provider = get_provider('mock')
        self.assertIsInstance(provider, MockProvider)

    def test_unknown_provider_raises(self):
        with self.assertRaises(ProviderNotFound) as ctx:
            get_provider('openai')
        self.assertIn('openai', str(ctx.exception))

    @override_settings(CONTENT_AI_PROVIDER='')
    def test_missing_configuration_raises(self):
        with self.assertRaises(ProviderConfigurationError):
            get_provider()


class MockProviderTests(SimpleTestCase):
    def setUp(self):
        self.provider = MockProvider()

    def test_generate_post_returns_deterministic_payload(self):
        result = self.provider.generate_post(topic='ignored')
        self.assertEqual(result['title'], MOCK_RESPONSE)
        self.assertEqual(result['content'], MOCK_RESPONSE)
        self.assertEqual(result['excerpt'], MOCK_RESPONSE)

    def test_generate_ad_returns_deterministic_payload(self):
        result = self.provider.generate_ad()
        self.assertEqual(result['title'], MOCK_RESPONSE)
        self.assertEqual(result['description'], MOCK_RESPONSE)

    def test_rewrite_summarize_translate_are_deterministic(self):
        self.assertEqual(self.provider.rewrite()['text'], MOCK_RESPONSE)
        self.assertEqual(self.provider.summarize()['summary'], MOCK_RESPONSE)
        self.assertEqual(self.provider.translate()['text'], MOCK_RESPONSE)

    def test_mock_provider_is_base_ai_provider(self):
        self.assertIsInstance(self.provider, BaseAIProvider)


class BaseAIProviderTests(SimpleTestCase):
    def test_base_methods_raise_not_implemented(self):
        provider = BaseAIProvider()
        for method_name in (
            'generate_post',
            'generate_ad',
            'rewrite',
            'summarize',
            'translate',
        ):
            with self.subTest(method=method_name):
                with self.assertRaises(NotImplementedError):
                    getattr(provider, method_name)()


class ProviderExceptionTests(SimpleTestCase):
    def test_exception_hierarchy(self):
        self.assertTrue(issubclass(ProviderNotFound, Exception))
        self.assertTrue(issubclass(ProviderConfigurationError, Exception))
        self.assertTrue(issubclass(GenerationError, Exception))
