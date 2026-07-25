"""Tests for AI Provider Platform (RFC-005) — keeps production providers compatible."""

from __future__ import annotations

from django.test import SimpleTestCase, override_settings

from content_ai.config.ai_engine import (
    ENABLE_PROVIDER_PLATFORM,
    FEATURE_FLAGS,
)
from content_ai.providers import (
    BaseAIProvider,
    CapabilityError,
    MockProvider,
    ProviderConfigurationError,
    ProviderFactory,
    ProviderManager,
    ProviderNotFound,
    ProviderRegistry,
    ProviderUnavailableError,
    get_provider,
    list_providers,
    register_provider,
)
from content_ai.providers.adapters.claude import ClaudeProvider
from content_ai.providers.capabilities import ProviderCapabilities
from content_ai.providers.models import ModelMetadata, UsageReport


class ProviderPlatformFlagTests(SimpleTestCase):
    def test_flag_disabled(self):
        self.assertFalse(ENABLE_PROVIDER_PLATFORM)
        self.assertFalse(FEATURE_FLAGS['ENABLE_PROVIDER_PLATFORM'])


class RegistryFactoryManagerTests(SimpleTestCase):
    def test_list_and_get_provider_compatible(self):
        self.assertEqual(list_providers(), ['mock', 'openai'])
        self.assertIsInstance(get_provider('mock'), MockProvider)

    def test_provider_registry_duplicate(self):
        registry = ProviderRegistry(initial={})
        registry.register('mock', MockProvider)
        with self.assertRaises(ProviderConfigurationError):
            registry.register('mock', MockProvider)

    def test_factory_create_mock(self):
        provider = ProviderFactory().create('mock')
        self.assertEqual(provider.name, 'mock')
        self.assertTrue(provider.health_check())

    @override_settings(CONTENT_AI_PROVIDER='')
    def test_factory_missing_config(self):
        with self.assertRaises(ProviderConfigurationError):
            ProviderFactory().create()

    def test_manager_generate_mock(self):
        manager = ProviderManager(default_provider='mock', max_retries=0)
        result = manager.generate('hello', task='post_generation')
        self.assertTrue(result.success)
        self.assertIsInstance(manager.last_usage(), UsageReport)

    def test_manager_capability_check(self):
        manager = ProviderManager(default_provider='mock')
        provider = manager.select_provider()
        with self.assertRaises(CapabilityError):
            manager.require_capability(provider, 'vision')

    def test_unknown_provider(self):
        with self.assertRaises(ProviderNotFound):
            ProviderFactory().create('not-real')


class CapabilitiesAndModelsTests(SimpleTestCase):
    def test_capabilities_model(self):
        caps = ProviderCapabilities(text_generation=True, streaming=False)
        self.assertTrue(caps.supports('text_generation'))
        self.assertFalse(caps.supports('streaming'))
        self.assertFalse(caps.supports('not_a_cap'))

    def test_mock_capabilities_and_models(self):
        provider = MockProvider()
        self.assertTrue(provider.capabilities().text_generation)
        models = provider.discover_models()
        self.assertEqual(models[0].model, 'mock')
        self.assertIsInstance(models[0], ModelMetadata)

    def test_base_stream_not_implemented(self):
        with self.assertRaises(NotImplementedError):
            BaseAIProvider().stream('x')


class AdapterStubTests(SimpleTestCase):
    def test_claude_stub_unavailable(self):
        with self.assertRaises(ProviderUnavailableError):
            ClaudeProvider()


class RegisterProviderTests(SimpleTestCase):
    def test_register_custom_provider(self):
        class TempProvider(BaseAIProvider):
            name = 'temp_rfc005'

            def generate_post(self, prompt=''):
                from content_ai.schemas.responses import GenerationResult

                return GenerationResult(
                    success=True,
                    content='temp',
                    provider=self.name,
                )

        # Use isolated registry to avoid polluting global list for other tests.
        registry = ProviderRegistry(initial={'mock': MockProvider})
        registry.register('temp_rfc005', TempProvider)
        self.assertIn('temp_rfc005', registry.list_providers())
