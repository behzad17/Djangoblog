"""Tests for Editorial Studio Smart News Import (ES-001A)."""

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
from content_ai.editorial_studio.services import (
    NewsImportService,
    detect_content_type,
    parse_structured_draft,
    source_name_from_domain,
)
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

STRUCTURED_BODY = """
TITLE:
مسکن در استکهلم
LEAD:
بازار مسکن در استکهلم همچنان پرتقاضا است.
BODY:
شهرداری برنامه‌های جدیدی برای ساخت مسکن اعلام کرده است.
SUMMARY:
تقاضای مسکن در استکهلم ادامه دارد.
CATEGORY:
news
TAGS:
مسکن, استکهلم, سوئد
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

    def test_extract_prefers_og_title_and_header_h1(self):
        html = """
        <html><head>
          <title>Noise | Example News</title>
          <meta property="og:title" content="Rätt bostadsnyhet" />
        </head>
        <body>
          <header><h1>Rätt bostadsnyhet</h1></header>
          <article>
            <p>Det är viktigt att förstå bostadsmarknaden och att följa utvecklingen.</p>
            <p>Kommunen planerar nya lägenheter för familjer under nästa år.</p>
          </article>
        </body></html>
        """
        article = extract_readable_content(
            html,
            url='https://www.example.se/nyheter/bostad',
        )
        self.assertEqual(article.title, 'Rätt bostadsnyhet')

    def test_extract_cleans_document_title_suffix(self):
        html = """
        <html><head><title>Housing update in Stockholm | Example News</title></head>
        <body>
          <article>
            <p>Det är viktigt att förstå bostadsmarknaden och att följa utvecklingen.</p>
            <p>Experter säger att efterfrågan fortsätter att öka i regionen.</p>
          </article>
        </body></html>
        """
        article = extract_readable_content(
            html,
            url='https://www.example.se/nyheter/bostad',
        )
        self.assertEqual(article.title, 'Housing update in Stockholm')

    def test_extract_fails_without_readable_body(self):
        with self.assertRaises(ArticleExtractionError):
            extract_readable_content(
                '<html><body><p>Hi</p></body></html>',
                url='https://example.se/x',
            )


class SmartImportHelperTests(SimpleTestCase):
    def test_parse_structured_draft(self):
        parsed = parse_structured_draft(STRUCTURED_BODY, fallback_title='X')
        self.assertEqual(parsed['title'], 'مسکن در استکهلم')
        self.assertIn('پرتقاضا', parsed['lead'])
        self.assertIn('شهرداری', parsed['body'])
        self.assertEqual(parsed['suggested_category'], 'news')
        self.assertEqual(parsed['suggested_tags'], ['مسکن', 'استکهلم', 'سوئد'])

    def test_parse_structured_draft_missing_body_does_not_dump_raw(self):
        parsed = parse_structured_draft(
            'TITLE:\nPersian title\nLEAD:\nPersian lead\n',
            fallback_title='Source',
        )
        self.assertEqual(parsed['title'], 'Persian title')
        self.assertEqual(parsed['lead'], 'Persian lead')
        self.assertEqual(parsed['body'], '')

    def test_detect_government_content_type(self):
        article = ExtractedArticle(
            url='https://www.skatteverket.se/press',
            title='Ny förordning',
            text='Regeringen och myndigheten meddelar nya regler.',
            domain='www.skatteverket.se',
            detected_language='sv',
        )
        self.assertEqual(detect_content_type(article), 'government')

    def test_source_name_from_domain(self):
        self.assertEqual(source_name_from_domain('www.svd.se'), 'SVD')
        self.assertEqual(
            source_name_from_domain('www.example.se'),
            'Example',
        )
        self.assertEqual(source_name_from_domain('127.0.0.1'), '127.0.0.1')

    def test_municipal_news_stays_news_not_government(self):
        article = ExtractedArticle(
            url='https://www.example.se/nyheter/bostad',
            title='Bostadsnyheter i Stockholm',
            text='Kommunen planerar nya lägenheter för familjer.',
            domain='www.example.se',
            detected_language='sv',
        )
        self.assertEqual(detect_content_type(article), 'news')


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

    def test_workflow_success_returns_structured_result_and_metadata(self):
        extracted = ExtractedArticle(
            url='https://www.example.se/nyheter/bostad',
            title='Bostadsnyheter i Stockholm',
            text='Det är viktigt att förstå bostadsmarknaden ' * 5,
            domain='www.example.se',
            detected_language='sv',
        )
        editorial = MagicMock()
        editorial.generate_draft.return_value = EditorialDraft(
            title='مسکن در استکهلم',
            lead='بازار مسکن در استکهلم همچنان پرتقاضا است.',
            body='شهرداری برنامه‌های جدیدی برای ساخت مسکن اعلام کرده است.',
            summary='تقاضای مسکن در استکهلم ادامه دارد.',
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
                'suggested_category': 'news',
                'suggested_tags': ['مسکن', 'استکهلم', 'سوئد'],
                'generation_passes': ['headline_lead', 'body'],
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
        result = service.import_news(
            'https://www.example.se/nyheter/bostad',
            content_type='auto',
            output_mode='publish_ready',
        )

        editorial.generate_draft.assert_called_once()
        kwargs = editorial.generate_draft.call_args.kwargs
        self.assertEqual(kwargs['language'], 'fa')
        self.assertEqual(kwargs['source'], extracted.url)
        self.assertEqual(kwargs['context'], extracted.text)
        self.assertEqual(kwargs['title'], extracted.title)
        self.assertIn('publish-ready Persian news draft', kwargs['instructions'])
        self.assertEqual(result['title'], 'مسکن در استکهلم')
        self.assertIn('پرتقاضا', result['lead'])
        self.assertIn('شهرداری', result['body'])
        self.assertEqual(result['suggested_category'], 'news')
        self.assertEqual(result['suggested_tags'], ['مسکن', 'استکهلم', 'سوئد'])
        self.assertEqual(result['source_url'], extracted.url)
        self.assertEqual(result['source_name'], 'Example')
        self.assertEqual(result['source_title'], extracted.title)
        self.assertEqual(result['language'], 'fa')
        self.assertEqual(result['source_language'], 'sv')
        self.assertEqual(result['content_type'], 'news')
        self.assertIn('drafting', result['workflow_stages'])
        self.assertEqual(result['provider'], 'mock')
        self.assertEqual(result['duration_ms'], 12.5)
        self.assertEqual(result['metadata']['provider'], 'mock')
        self.assertNotIn('intelligence', result['metadata'])

    def test_educational_output_mode_changes_instructions(self):
        extracted = ExtractedArticle(
            url='https://www.example.se/nyheter/bostad',
            title='Title',
            text='Det är viktigt att förstå bostadsmarknaden ' * 5,
            domain='www.example.se',
            detected_language='sv',
        )
        editorial = MagicMock()
        editorial.generate_draft.return_value = EditorialDraft(
            title='Title',
            body=STRUCTURED_BODY,
            language='fa',
            metadata={'workflow_stages': ['research', 'drafting']},
            telemetry=AIExecutionTelemetry(provider='mock', duration_ms=1),
        )
        service = NewsImportService(
            editorial=editorial,
            extractor=lambda url: extracted,
        )
        service.import_news(
            extracted.url,
            content_type='news',
            output_mode='educational',
        )
        instructions = editorial.generate_draft.call_args.kwargs['instructions']
        self.assertIn('educational Persian article', instructions)

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
        self.assertContains(response, 'Content Type')
        self.assertContains(response, 'Publish-ready News')
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
        self.assertIn(payload['error']['code'], {'invalid_url', 'extraction_failed'})

    @patch('content_ai.editorial_studio.views.NewsImportService.import_news')
    def test_api_success(self, mocked_import):
        mocked_import.return_value = {
            'title': 'Title',
            'lead': 'Lead',
            'body': 'Body',
            'short_summary': 'Summary',
            'suggested_category': 'news',
            'suggested_tags': ['a', 'b'],
            'source_url': 'https://www.example.se/a',
            'source_name': 'Example',
            'language': 'sv',
            'workflow_stages': ['research', 'drafting'],
            'provider': 'mock',
            'duration_ms': 3,
            'metadata': {
                'source_url': 'https://www.example.se/a',
                'provider': 'mock',
                'duration_ms': 3,
                'workflow_stages': ['research', 'drafting'],
            },
        }
        response = self.client.post(
            self.api_url,
            data=(
                '{"url":"https://www.example.se/a",'
                '"content_type":"news","output_mode":"summary"}'
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(payload['result']['body'], 'Body')
        mocked_import.assert_called_once()
        kwargs = mocked_import.call_args.kwargs
        self.assertEqual(kwargs['content_type'], 'news')
        self.assertEqual(kwargs['output_mode'], 'summary')

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
        self.assertIn('try again', response.json()['error']['message'].lower())
