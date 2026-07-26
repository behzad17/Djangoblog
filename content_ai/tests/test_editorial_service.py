from unittest.mock import MagicMock

from django.test import SimpleTestCase, override_settings

from content_ai.editorial import EditorialAIService, EditorialDraft
from content_ai.providers.exceptions import GenerationError
from content_ai.providers.mock import MOCK_RESPONSE
from content_ai.schemas.responses import GenerationResult
from content_ai.telemetry import AIExecutionTelemetry


HEAD_CONTENT = """TITLE:
مسکن در استکهلم
LEAD:
بازار مسکن در استکهلم همچنان پرتقاضا است.
"""

BODY_CONTENT = """BODY:
شهرداری برنامه‌های جدیدی برای ساخت مسکن اعلام کرده است.
SUMMARY:
تقاضای مسکن در استکهلم ادامه دارد.
CATEGORY:
news
TAGS:
مسکن, استکهلم
"""


@override_settings(CONTENT_AI_PROVIDER='mock')
class EditorialAIServiceTests(SimpleTestCase):
    def setUp(self):
        self.service = EditorialAIService()

    def test_generate_draft_runs_headline_lead_before_body(self):
        generation = MagicMock()
        generation.generate.side_effect = [
            GenerationResult(
                success=True,
                content=HEAD_CONTENT,
                metadata={'workflow_stages': ['research', 'drafting']},
                provider='mock',
                telemetry=AIExecutionTelemetry(
                    provider='mock',
                    duration_ms=2.0,
                    success=True,
                ),
            ),
            GenerationResult(
                success=True,
                content=BODY_CONTENT,
                metadata={'workflow_stages': ['research', 'drafting']},
                warnings=['note'],
                provider='mock',
                telemetry=AIExecutionTelemetry(
                    provider='mock',
                    duration_ms=3.0,
                    success=True,
                ),
            ),
        ]
        service = EditorialAIService(generation_service=generation)

        draft = service.generate_draft(
            title='Bostadsnyheter i Stockholm',
            language='fa',
            source='https://example.se/a',
            category='news',
            context='source text',
            instructions='publish-ready',
        )

        self.assertEqual(generation.generate.call_count, 2)
        first_req = generation.generate.call_args_list[0].args[1]
        second_req = generation.generate.call_args_list[1].args[1]
        self.assertIn('ONLY the Persian headline/title and opening', first_req.instructions)
        self.assertIn('Do NOT write the article body yet', first_req.instructions)
        self.assertIn('Bostadsnyheter i Stockholm', first_req.instructions)
        self.assertIn('Locked TITLE', second_req.instructions)
        self.assertIn('مسکن در استکهلم', second_req.instructions)
        self.assertIn('Do NOT rewrite TITLE or LEAD', second_req.instructions)
        self.assertEqual(draft.metadata.get('content_type'), 'news')
        self.assertEqual(draft.metadata.get('template_id'), 'news.v1')

        self.assertEqual(draft.title, 'مسکن در استکهلم')
        self.assertIn('پرتقاضا', draft.lead)
        self.assertIn('شهرداری', draft.body)
        self.assertIn('تقاضای', draft.summary)
        self.assertEqual(draft.language, 'fa')
        self.assertEqual(draft.metadata.get('generation_passes'), ['headline_lead', 'body'])
        self.assertEqual(draft.metadata.get('source_title'), 'Bostadsnyheter i Stockholm')
        self.assertEqual(draft.metadata.get('suggested_tags'), ['مسکن', 'استکهلم'])
        self.assertEqual(draft.telemetry.duration_ms, 5.0)

    def test_generate_draft_with_mock_provider_two_passes(self):
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
        # Mock returns unlabelled text; first-line lead becomes working title.
        self.assertEqual(draft.title, MOCK_RESPONSE)
        self.assertEqual(draft.lead, MOCK_RESPONSE)
        self.assertEqual(draft.body, MOCK_RESPONSE)
        self.assertEqual(draft.language, 'sv')
        self.assertEqual(draft.metadata.get('provider'), 'mock')
        self.assertEqual(
            draft.metadata.get('generation_passes'),
            ['headline_lead', 'body'],
        )
        self.assertIsNotNone(draft.telemetry)
        self.assertEqual(draft.telemetry.provider, 'mock')
        self.assertTrue(draft.telemetry.success)

    def test_provider_errors_propagate(self):
        generation = MagicMock()
        generation.generate.side_effect = GenerationError('provider failed')
        service = EditorialAIService(generation_service=generation)

        with self.assertRaises(GenerationError) as ctx:
            service.generate_draft(title='T')
        self.assertIn('provider failed', str(ctx.exception))

    def test_none_content_becomes_empty_sections(self):
        generation = MagicMock()
        generation.generate.side_effect = [
            GenerationResult(success=True, content=None, provider='mock'),
            GenerationResult(success=True, content=None, provider='mock'),
        ]
        service = EditorialAIService(generation_service=generation)

        draft = service.generate_draft(title='T')
        self.assertEqual(draft.title, 'T')
        self.assertEqual(draft.lead, '')
        self.assertEqual(draft.body, '')


class EditorialDraftTests(SimpleTestCase):
    def test_draft_defaults(self):
        draft = EditorialDraft()
        self.assertEqual(draft.title, '')
        self.assertEqual(draft.lead, '')
        self.assertEqual(draft.body, '')
        self.assertEqual(draft.summary, '')
        self.assertEqual(draft.language, '')
        self.assertEqual(draft.metadata, {})
        self.assertIsNone(draft.telemetry)
