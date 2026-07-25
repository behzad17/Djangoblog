"""Tests for Editorial Studio News Import (ES-001)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from content_ai.config.ai_engine import (
    ENABLE_EDITORIAL_STUDIO,
    FEATURE_FLAGS,
)
from content_ai.editorial.drafts import EditorialDraft
from content_ai.editorial_studio.services import NewsImportService
from content_ai.providers.exceptions import GenerationError
from content_ai.source.extract import (
    ArticleExtractionError,
    ExtractedArticle,
    extract_readable_content,
    validate_news_url,
)
from content_ai.telemetry import AIExecutionTelemetry


SAMPLE_HTML = """
<html><head><title>Bostadsnyheter i Stockholm</title></head>
<body>
<article>
  <h1>Bostadsnyheter i Stockholm</h1>
  <p>Det är viktigt att förstå bostadsmarknaden och att följa utvecklingen.</p>
  <p>Kommunen planerar nya lägenheter för familjer under nästa år.</p>
  <p>Experter säger att efterfrågan fortsätter att öka i regionen.</p>
</article>
</body></html>
"""


class EditorialStudioFlagTests(SimpleTestCase):
    def test_editorial_studio_enabled(self):
        self.assertTrue(ENABLE_EDITORIAL_STUDIO)
        self.assertTrue(FEATURE_FLAGS['ENABLE_EDITORIAL_STUDIO'])


class ExtractorTests(SimpleTestCase):
    def test_validate_rejects_empty_and_non_http(self):
        with self.assertRaises(ArticleExtractionError):
            validate_news_url('')
        with self.assertRaises(ArticleExtractionError):
            validate_news_url('ftp://example.com/a')
        with self.assertRaises(ArticleExtractionError):
            validate_news_url('not-a-url')

    def test_extract_readable_content_from_html(self):
        article = extract_readable_content(
            SAMPLE_HTML,
            url='https://www.example.se/nyheter/bostad',
        )
        self.assertEqual(article.domain, 'www.example.se')
        self.assertIn('Bostadsnyheter', article.title)
        self.assertIn('bostadsmarknaden', article.text)
        self.assertEqual(article.detected_language, 'sv')

    def test_extract_fails_without_readable_body(self):
        with self.assertRaises(ArticleExtractionError):
            extract_readable_content(
                '<html><body><p>Hi</p></body></html>',
                url='https://example.se/x',
            )


class NewsImportServiceTests(SimpleTestCase):
    def test_invalid_url_raises_extraction_error(self):
        service = NewsImportService()
        with self.assertRaises(ArticleExtractionError):
            service.import_news('not-a-url')

    def test_extraction_failure_propagates(self):
        def boom(_url):
            raise ArticleExtractionError('Could not extract readable content.')

        service = NewsImportService(extractor=boom)
        with self.assertRaises(ArticleExtractionError):
            service.import_news('https://www.example.se/nyheter/x')

    def test_workflow_success_returns_persian_draft_and_metadata(self):
        extracted = ExtractedArticle(
            url='https://www.example.se/nyheter/bostad',
            title='Bostadsnyheter i Stockholm',
            text='Det är viktigt att förstå bostadsmarknaden ' * 5,
            domain='www.example.se',
            detected_language='sv',
        )
        editorial = MagicMock()
        editorial.generate_draft.return_value = EditorialDraft(
            title='Bostadsnyheter i Stockholm',
            body='پیش‌نویس فارسی درباره مسکن در استکهلم',
            language='fa',
            metadata={
                'provider': 'mock',
                'workflow_stages': [
                    'research',
                    'source_intelligence',
                    'knowledge',
                    'drafting',
                    'evaluation',
                ],
                'workflow_state': 'drafting',
                'prompt_version': 'v1',
                'warnings': [],
            },
            telemetry=AIExecutionTelemetry(
                provider='mock',
                duration_ms=12.5,
                success=True,
            ),
        )
        service = NewsImportService(
            editorial=editorial,
            extractor=lambda url: extracted,
        )
        result = service.import_news('https://www.example.se/nyheter/bostad')

        editorial.generate_draft.assert_called_once()
        kwargs = editorial.generate_draft.call_args.kwargs
        self.assertEqual(kwargs['language'], 'fa')
        self.assertEqual(kwargs['source'], extracted.url)
        self.assertEqual(kwargs['context'], extracted.text)
        self.assertEqual(result['draft'], 'پیش‌نویس فارسی درباره مسکن در استکهلم')
        self.assertEqual(result['source']['domain'], 'www.example.se')
        self.assertEqual(result['metadata']['detected_language'], 'sv')
        self.assertIn('drafting', result['metadata']['workflow_stages'])
        self.assertEqual(result['metadata']['provider'], 'mock')
        self.assertEqual(result['metadata']['duration_ms'], 12.5)

    def test_workflow_failure_propagates(self):
        extracted = ExtractedArticle(
            url='https://www.example.se/nyheter/bostad',
            title='Title',
            text='Det är viktigt att förstå bostadsmarknaden ' * 5,
            domain='www.example.se',
            detected_language='sv',
        )
        editorial = MagicMock()
        editorial.generate_draft.side_effect = GenerationError('boom')
        service = NewsImportService(
            editorial=editorial,
            extractor=lambda url: extracted,
        )
        with self.assertRaises(GenerationError):
            service.import_news('https://www.example.se/nyheter/bostad')


@override_settings(
    ROOT_URLCONF='codestar.urls',
    CONTENT_AI_PROVIDER='mock',
)
class EditorialStudioViewTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.staff = User.objects.create_user(
            username='es-staff',
            password='pass',
            is_staff=True,
        )
        self.client = Client()
        self.client.force_login(self.staff)
        self.page_url = reverse('content_ai:editorial_studio')
        self.api_url = reverse('content_ai:editorial_studio_import')

    def test_staff_can_open_news_import_page(self):
        response = self.client.get(self.page_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'News Import')
        self.assertContains(response, 'Generate Draft')

    def test_invalid_url_returns_clean_error(self):
        response = self.client.post(
            self.api_url,
            data='{"url":"not-a-url"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertIn('error', payload)
        self.assertEqual(payload['error']['code'], 'extraction_failed')

    @patch('content_ai.editorial_studio.views.NewsImportService.import_news')
    def test_api_success(self, mocked_import):
        mocked_import.return_value = {
            'source': {
                'url': 'https://www.example.se/a',
                'domain': 'www.example.se',
                'detected_language': 'sv',
            },
            'title': 'Title',
            'draft': 'متن فارسی',
            'language': 'fa',
            'metadata': {
                'workflow_stages': ['research', 'drafting'],
                'provider': 'mock',
                'duration_ms': 3,
            },
        }
        response = self.client.post(
            self.api_url,
            data='{"url":"https://www.example.se/a"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['result']['draft'], 'متن فارسی')

    @patch('content_ai.editorial_studio.views.NewsImportService.import_news')
    def test_api_extraction_failure(self, mocked_import):
        mocked_import.side_effect = ArticleExtractionError(
            'Could not extract readable article content from this page.'
        )
        response = self.client.post(
            self.api_url,
            data='{"url":"https://www.example.se/empty"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'extraction_failed')

    @patch('content_ai.editorial_studio.views.NewsImportService.import_news')
    def test_api_workflow_failure(self, mocked_import):
        mocked_import.side_effect = GenerationError('provider failed')
        response = self.client.post(
            self.api_url,
            data='{"url":"https://www.example.se/a"}',
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['error']['code'], 'generation_failed')
