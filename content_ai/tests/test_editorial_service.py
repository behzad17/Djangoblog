from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings

from content_ai.editorial import EditorialAIService, EditorialDraft
from content_ai.providers.exceptions import GenerationError
from content_ai.providers.mock import MOCK_RESPONSE
from content_ai.schemas.responses import GenerationResult
from content_ai.telemetry import AIExecutionTelemetry


@override_settings(CONTENT_AI_PROVIDER='mock')
class EditorialAIServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = EditorialAIService()

    def test_generate_draft_returns_editorial_draft(self):
        draft = self.service.generate_draft(
            title='Housing news',
            language='sv',
            source='sandbox',
            category='news',
            context='local',
            instructions='short',
            provider_name='mock',
        )
        self.assertIsInstance(draft, EditorialDraft)
        self.assertEqual(draft.title, 'Housing news')
        self.assertEqual(draft.body, MOCK_RESPONSE)
        self.assertEqual(draft.summary, '')
        self.assertEqual(draft.language, 'sv')
        self.assertEqual(draft.metadata.get('provider'), 'mock')
        self.assertTrue(draft.metadata.get('success'))
        self.assertIsNotNone(draft.telemetry)
        self.assertEqual(draft.telemetry.provider, 'mock')
        self.assertTrue(draft.telemetry.success)

    def test_conversion_maps_generation_result_fields(self):
        generation = MagicMock()
        generation.generate.return_value = GenerationResult(
            success=True,
            content='Body text',
            metadata={'task': 'post_generation', 'model': 'x'},
            warnings=['note'],
            provider='mock',
            telemetry=AIExecutionTelemetry(provider='mock', success=True),
        )
        service = EditorialAIService(generation_service=generation)

        draft = service.generate_draft(title='T', language='fa')

        self.assertEqual(draft.title, 'T')
        self.assertEqual(draft.body, 'Body text')
        self.assertEqual(draft.language, 'fa')
        self.assertEqual(draft.metadata['task'], 'post_generation')
        self.assertEqual(draft.metadata['provider'], 'mock')
        self.assertEqual(draft.metadata['warnings'], ['note'])
        self.assertTrue(draft.metadata['success'])
        self.assertIsNotNone(draft.telemetry)
        self.assertEqual(draft.telemetry.provider, 'mock')

    def test_provider_errors_propagate(self):
        generation = MagicMock()
        generation.generate.side_effect = GenerationError('provider failed')
        service = EditorialAIService(generation_service=generation)

        with self.assertRaises(GenerationError) as ctx:
            service.generate_draft(title='T')
        self.assertIn('provider failed', str(ctx.exception))

    def test_none_content_becomes_empty_body(self):
        generation = MagicMock()
        generation.generate.return_value = GenerationResult(
            success=True,
            content=None,
            provider='mock',
        )
        service = EditorialAIService(generation_service=generation)

        draft = service.generate_draft(title='T')
        self.assertEqual(draft.body, '')


class EditorialDraftTests(SimpleTestCase):
    def test_draft_defaults(self):
        draft = EditorialDraft()
        self.assertEqual(draft.title, '')
        self.assertEqual(draft.body, '')
        self.assertEqual(draft.summary, '')
        self.assertEqual(draft.language, '')
        self.assertEqual(draft.metadata, {})
        self.assertIsNone(draft.telemetry)
