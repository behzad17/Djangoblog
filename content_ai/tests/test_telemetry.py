from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, override_settings

from content_ai.constants import AIGenerationTask
from content_ai.providers.exceptions import GenerationError
from content_ai.providers.mock import MOCK_MODEL, MOCK_RESPONSE, MockProvider
from content_ai.schemas import GenerationResult, PostGenerationRequest
from content_ai.services.generation import ContentGenerationService
from content_ai.telemetry import AIExecutionTelemetry, merge_telemetry


class AIExecutionTelemetryTests(SimpleTestCase):
    def test_defaults(self):
        telemetry = AIExecutionTelemetry()
        self.assertEqual(telemetry.provider, '')
        self.assertEqual(telemetry.model, '')
        self.assertIsNone(telemetry.started_at)
        self.assertIsNone(telemetry.finished_at)
        self.assertIsNone(telemetry.duration_ms)
        self.assertTrue(telemetry.success)
        self.assertIsNone(telemetry.error_type)
        self.assertEqual(telemetry.prompt_length, 0)
        self.assertEqual(telemetry.response_length, 0)
        self.assertIsNone(telemetry.token_usage)
        self.assertIsNone(telemetry.estimated_cost)
        self.assertEqual(telemetry.metadata, {})

    def test_merge_telemetry_preserves_and_updates(self):
        existing = AIExecutionTelemetry(
            provider='mock',
            model='mock',
            prompt_length=10,
            token_usage={'total_tokens': 3},
        )
        merged = merge_telemetry(
            existing,
            duration_ms=12.5,
            success=True,
            started_at=None,
        )
        self.assertEqual(merged.provider, 'mock')
        self.assertEqual(merged.model, 'mock')
        self.assertEqual(merged.prompt_length, 10)
        self.assertEqual(merged.token_usage, {'total_tokens': 3})
        self.assertEqual(merged.duration_ms, 12.5)


class GenerationResultTelemetryTests(SimpleTestCase):
    def test_telemetry_defaults_to_none(self):
        result = GenerationResult(success=True, content='x')
        self.assertIsNone(result.telemetry)

    def test_telemetry_can_be_attached(self):
        telemetry = AIExecutionTelemetry(provider='mock', duration_ms=1.0)
        result = GenerationResult(
            success=True,
            content='x',
            telemetry=telemetry,
        )
        self.assertEqual(result.telemetry.provider, 'mock')
        self.assertEqual(result.telemetry.duration_ms, 1.0)


@override_settings(CONTENT_AI_PROVIDER='mock')
class GenerationServiceTelemetryTests(SimpleTestCase):
    def setUp(self):
        self.service = ContentGenerationService()

    def test_successful_generation_attaches_duration_and_success(self):
        result = self.service.generate(
            AIGenerationTask.POST_GENERATION,
            PostGenerationRequest(title='T'),
            provider_name='mock',
        )
        self.assertIsNotNone(result.telemetry)
        self.assertTrue(result.telemetry.success)
        self.assertIsNone(result.telemetry.error_type)
        self.assertEqual(result.telemetry.provider, 'mock')
        self.assertEqual(result.telemetry.model, MOCK_MODEL)
        self.assertIsNotNone(result.telemetry.started_at)
        self.assertIsNotNone(result.telemetry.finished_at)
        self.assertIsNotNone(result.telemetry.duration_ms)
        self.assertGreaterEqual(result.telemetry.duration_ms, 0)
        self.assertEqual(result.telemetry.response_length, len(MOCK_RESPONSE))
        self.assertGreater(result.telemetry.prompt_length, 0)

    def test_telemetry_propagates_from_mock_provider(self):
        result = self.service.generate(
            AIGenerationTask.POST_GENERATION,
            PostGenerationRequest(title='Propagate'),
            provider_name='mock',
        )
        self.assertEqual(result.telemetry.metadata.get('source'), 'mock')

    def test_provider_error_includes_failure_telemetry(self):
        provider = MagicMock(spec=MockProvider)
        provider.name = 'mock'
        provider.generate_post.side_effect = GenerationError('boom')

        with patch(
            'content_ai.services.generation.get_provider',
            return_value=provider,
        ):
            with self.assertRaises(GenerationError) as ctx:
                self.service.generate(
                    AIGenerationTask.POST_GENERATION,
                    PostGenerationRequest(title='T'),
                )

        self.assertIsNotNone(ctx.exception.telemetry)
        self.assertFalse(ctx.exception.telemetry.success)
        self.assertEqual(ctx.exception.telemetry.error_type, 'GenerationError')
        self.assertIsNotNone(ctx.exception.telemetry.duration_ms)
        self.assertGreaterEqual(ctx.exception.telemetry.duration_ms, 0)
