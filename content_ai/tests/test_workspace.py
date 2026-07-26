"""Tests for AI Editorial Workspace (APF-001)."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from django.contrib.auth import get_user_model
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from content_ai.config.ai_engine import (
    ENABLE_AI_EDITORIAL_WORKSPACE,
    FEATURE_FLAGS,
)
from content_ai.editorial.drafts import EditorialDraft
from content_ai.source.extract import ArticleExtractionError, ExtractedArticle
from content_ai.source.inspector import SourceInspector
from content_ai.workflow.states import WorkflowState
from content_ai.workspace.actions import get_action, list_actions_for_ui
from content_ai.workspace.integrity import SourceIntegrityError
from content_ai.workspace.services import WorkspaceService
from content_ai.workspace.session import ArticleSections, WorkspaceSession

User = get_user_model()


class WorkspaceFlagTests(SimpleTestCase):
    def test_workspace_flag_enabled(self):
        self.assertTrue(ENABLE_AI_EDITORIAL_WORKSPACE)
        self.assertTrue(FEATURE_FLAGS['ENABLE_AI_EDITORIAL_WORKSPACE'])


class WorkspaceSessionTests(SimpleTestCase):
    def test_sections_roundtrip(self):
        sections = ArticleSections(
            headline='H',
            lead='L',
            body='B',
            summary='S',
            tags=['a', 'b'],
        )
        restored = ArticleSections.from_dict(sections.to_dict())
        self.assertEqual(restored.headline, 'H')
        self.assertEqual(restored.tags, ['a', 'b'])

    def test_history_restore(self):
        session = WorkspaceSession()
        session.sections.headline = 'v1'
        session.push_history('First')
        session.sections.headline = 'v2'
        session.push_history('Second')
        entry_id = session.history[0].entry_id
        self.assertTrue(session.restore_history(entry_id))
        self.assertEqual(session.sections.headline, 'v1')
        self.assertFalse(session.to_dict()['auto_publish_allowed'])


class WorkspaceActionsTests(SimpleTestCase):
    def test_catalogue_has_core_actions(self):
        ids = {a['id'] for a in list_actions_for_ui()}
        self.assertIn('improve_headline', ids)
        self.assertIn('prepare_seo', ids)
        action = get_action('related_topics')
        self.assertIsNotNone(action)
        self.assertFalse(action.implemented)

    def test_actions_filter_by_content_type(self):
        guide_ids = {a['id'] for a in list_actions_for_ui('guide')}
        self.assertIn('improve_instructions', guide_ids)
        news_ids = {a['id'] for a in list_actions_for_ui('news')}
        self.assertNotIn('condense_answers', news_ids)


class WorkspaceServiceTests(SimpleTestCase):
    def test_ingest_source_sets_research(self):
        service = WorkspaceService()
        session = service.new_session()
        source = service.ingest_source(
            session,
            text='متن فارسی برای تست',
            title='Test',
            publisher='Peyvand',
        )
        self.assertEqual(source['publisher'], 'Peyvand')
        self.assertEqual(session.workflow_state, WorkflowState.RESEARCHING)
        self.assertIn('Source:', session.research_notes)
        self.assertFalse(session.to_dict()['auto_publish_allowed'])
        self.assertTrue(session.pipeline.get('source_imported'))
        self.assertTrue(session.pipeline.get('content_classified'))
        self.assertTrue(session.pipeline.get('style_detected'))
        self.assertIn('classification', session.metadata)
        self.assertTrue(session.content_type)
        self.assertTrue(session.writing_style)
        self.assertIn('style', session.metadata['classification'])

    def test_ingest_url_fetches_and_fills_source_text(self):
        article = ExtractedArticle(
            url='https://www.example.se/nyheter/bostad',
            title='Bostadsnyheter i Stockholm',
            text=(
                'Det är viktigt att förstå bostadsmarknaden och att följa '
                'utvecklingen. Kommunen planerar nya lägenheter för familjer.'
            ),
            domain='www.example.se',
            detected_language='sv',
            publisher='Example',
            publication_date=__import__('datetime').date(2026, 7, 1),
            detected_country='SE',
            metadata={'extractor': 'test'},
        )
        inspector = SourceInspector(extractor=lambda url: article)
        service = WorkspaceService(source_inspector=inspector)
        session = service.new_session()
        source = service.ingest_source(
            session,
            url='https://www.example.se/nyheter/bostad',
            text='',
        )
        self.assertEqual(source['retrieval'], 'url_fetch')
        self.assertIn('bostadsmarknaden', session.source_material)
        self.assertEqual(session.source_url, article.url)
        self.assertEqual(source['title'], article.title)
        self.assertEqual(source['publisher'], 'Example')
        self.assertEqual(source['publication_date'], '2026-07-01')
        self.assertEqual(source['detected_country'], 'SE')
        self.assertIn('Bostadsnyheter', session.research_notes)
        self.assertIn('Fetched and extracted', session.last_explanations[0])

    def test_ingest_url_extraction_failure_raises(self):
        def boom(url):
            raise ArticleExtractionError(
                'Unable to extract article content from this URL.\n'
                'Paste the article text manually.'
            )

        service = WorkspaceService(
            source_inspector=SourceInspector(extractor=boom)
        )
        session = service.new_session()
        with self.assertRaises(ArticleExtractionError) as ctx:
            service.ingest_source(
                session,
                url='https://www.example.se/empty',
                text='',
            )
        self.assertIn('Unable to extract article content', str(ctx.exception))
        self.assertEqual(session.source_material, '')

    def test_set_classification_override(self):
        service = WorkspaceService()
        session = service.new_session()
        service.ingest_source(
            session,
            text='A short news update about housing.',
            title='Housing update',
        )
        service.set_classification(
            session,
            content_type='guide',
            goal='teach',
            writing_style='educational',
        )
        self.assertEqual(session.resolved_content_type(), 'guide')
        self.assertEqual(session.resolved_goal(), 'teach')
        self.assertEqual(session.resolved_writing_style(), 'educational')
        self.assertEqual(session.template_id, 'guide.v1')
        payload = session.to_dict()
        self.assertEqual(payload['lead_label'], 'Introduction')
        self.assertEqual(payload['content_type_override'], 'guide')
        self.assertEqual(payload['writing_style_override'], 'educational')
        self.assertEqual(payload['prompt_version'], 'v1')

    def test_generate_draft_passes_content_type(self):
        editorial = MagicMock()
        editorial.generate_draft.return_value = EditorialDraft(
            title='Guide title',
            lead='Intro',
            body='Steps',
            summary='Sum',
            language='fa',
            metadata={'suggested_tags': ['a']},
        )
        service = WorkspaceService(editorial=editorial)
        session = service.new_session()
        service.set_classification(
            session,
            content_type='guide',
            goal='teach',
            writing_style='educational',
        )
        session.source_material = 'How to apply for support steg för steg'
        service.generate_draft(session, title='Guide')
        kwargs = editorial.generate_draft.call_args.kwargs
        self.assertEqual(kwargs['content_type'], 'guide')
        self.assertEqual(kwargs['goal'], 'teach')
        self.assertEqual(kwargs['style'], 'educational')
        self.assertTrue(session.pipeline.get('draft_generated'))
        self.assertEqual(session.sections.headline, 'Guide title')
        self.assertEqual(session.sections.lead, 'Intro')

    def test_generate_draft_rejects_empty_source(self):
        service = WorkspaceService(editorial=MagicMock())
        session = service.new_session()
        session.sections.headline = 'Stale headline from previous article'
        session.source_url = 'https://example.se/new-url'
        with self.assertRaises(SourceIntegrityError) as ctx:
            service.generate_draft(session, title='')
        self.assertIn('not been imported', str(ctx.exception))
        service.editorial.generate_draft.assert_not_called()

    def test_generate_draft_rejects_url_only_ingest(self):
        service = WorkspaceService(
            editorial=MagicMock(),
            source_inspector=SourceInspector(
                extractor=lambda url: (_ for _ in ()).throw(
                    ArticleExtractionError(
                        'Unable to extract article content from this URL.\n'
                        'Paste the article text manually.'
                    )
                )
            ),
        )
        session = service.new_session()
        session.sections = ArticleSections(
            headline='Old article',
            lead='Old lead',
            body='Old body about topic A',
        )
        session.source_material = 'Article A full text about housing.'
        session.source_url = 'https://example.se/article-a'
        with self.assertRaises(ArticleExtractionError):
            service.ingest_source(
                session,
                url='https://example.se/article-b',
                text='',
                title='',
            )
        # Failed fetch must not silently continue with old material under new URL.
        self.assertEqual(session.source_url, 'https://example.se/article-a')
        self.assertIn('housing', session.source_material.lower())

    def test_generate_does_not_reuse_previous_material_for_new_url(self):
        editorial = MagicMock()
        editorial.generate_draft.return_value = EditorialDraft(
            title='Should not run',
            lead='',
            body='',
            summary='',
            language='fa',
            metadata={},
        )

        def extractor(url):
            raise ArticleExtractionError(
                'Unable to extract article content from this URL.\n'
                'Paste the article text manually.'
            )

        service = WorkspaceService(
            editorial=editorial,
            source_inspector=SourceInspector(extractor=extractor),
        )
        session = service.new_session()
        service.ingest_source(
            session,
            url='https://example.se/a',
            text='Source article A about taxes.',
            title='Taxes',
        )
        with self.assertRaises(ArticleExtractionError):
            service.ingest_source(
                session,
                url='https://example.se/b',
                text='',
                title='',
            )
        editorial.generate_draft.assert_not_called()
        self.assertIn('taxes', session.source_material.lower())
        self.assertEqual(session.source_url, 'https://example.se/a')

    def test_seo_placeholders(self):
        service = WorkspaceService()
        session = service.new_session()
        session.sections.headline = 'Title here'
        session.sections.summary = 'Summary here'
        session.sections.tags = ['sweden']
        report = service.seo_placeholders(session)
        self.assertEqual(report['seo_title'], 'Title here')
        self.assertIn('placeholder', report['note'].lower())

    def test_regenerate_section_keeps_other_fields(self):
        editorial = MagicMock()
        editorial.generate_draft.return_value = EditorialDraft(
            title='New headline only',
            body='Lead paragraph.\n\nBody stays mocked.',
            summary='Sum',
            language='fa',
            metadata={},
        )
        service = WorkspaceService(editorial=editorial)
        session = service.new_session()
        session.sections = ArticleSections(
            headline='Old',
            lead='Old lead',
            body='Old body',
            summary='Old summary',
        )
        service.regenerate_section(session, 'headline')
        self.assertEqual(session.sections.headline, 'New headline only')
        self.assertEqual(session.sections.body, 'Old body')
        self.assertEqual(session.sections.summary, 'Old summary')

    def test_workflow_blocks_publish(self):
        service = WorkspaceService()
        session = service.new_session()
        session.workflow_state = WorkflowState.APPROVED
        with self.assertRaises(ValueError):
            service.advance_workflow(session, WorkflowState.PUBLISHED)

    def test_fact_check_empty(self):
        service = WorkspaceService()
        session = service.new_session()
        report = service.fact_check(session)
        self.assertEqual(report['summary']['claim_count'], 0)
        self.assertFalse(report['summary']['auto_publish_allowed'])

    def test_evaluate_runs(self):
        service = WorkspaceService()
        session = service.new_session()
        session.sections.body = 'A short body for evaluation heuristics.'
        report = service.evaluate(session)
        self.assertIn('overall', report)
        self.assertIn('scores', report)

    def test_unimplemented_assistant_action(self):
        service = WorkspaceService()
        session = service.new_session()
        service.run_assistant_action(session, 'related_topics')
        self.assertIn('future', session.last_explanations[0].lower())


@override_settings(CONTENT_AI_PROVIDER='mock')
class WorkspaceViewPermissionTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('content_ai:editorial_workspace')
        self.api = reverse(
            'content_ai:workspace_api', kwargs={'action': 'reset'}
        )
        self.user = User.objects.create_user(
            username='wsuser', password='password123'
        )
        self.staff = User.objects.create_user(
            username='wsstaff', password='password123', is_staff=True
        )

    def test_anonymous_redirected(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)

    def test_non_staff_forbidden(self):
        self.client.login(username='wsuser', password='password123')
        response = self.client.get(self.url)
        self.assertIn(response.status_code, (302, 403))

    def test_staff_can_open_workspace(self):
        self.client.login(username='wsstaff', password='password123')
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Editorial Workspace')

    def test_api_requires_staff(self):
        response = self.client.post(
            self.api,
            data=json.dumps({}),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)


@override_settings(CONTENT_AI_PROVIDER='mock', ADMIN_NOTIFICATION_ENABLED=False)
class WorkspaceAPIIntegrationTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.staff = User.objects.create_user(
            username='wsapistaff', password='password123', is_staff=True
        )
        self.client.login(username='wsapistaff', password='password123')

    def _post(self, action, payload=None):
        url = reverse('content_ai:workspace_api', kwargs={'action': action})
        return self.client.post(
            url,
            data=json.dumps(payload or {}),
            content_type='application/json',
        )

    def test_ingest_and_update_sections(self):
        response = self._post(
            'ingest_source',
            {
                'source_text': 'Source text for workspace',
                'title': 'Src',
                'publisher': 'TestPub',
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(data['session']['workflow_state'], 'researching')

        response = self._post(
            'update_sections',
            {
                'sections': {'headline': 'Edited', 'body': 'Body text'},
                'research_notes': 'Note',
            },
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['session']['sections']['headline'], 'Edited')
        self.assertEqual(data['session']['research_notes'], 'Note')

    def test_generate_draft_with_mock(self):
        response = self._post(
            'generate_draft',
            {
                'source_text': 'Context about housing in Sweden.',
                'title': 'Housing',
            },
        )
        if response.status_code != 200:
            self.fail(response.content.decode('utf-8')[:800])
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertTrue(data['session']['sections']['body'] or data['session']['sections']['headline'])
        self.assertFalse(data['session']['auto_publish_allowed'])
        self.assertEqual(
            data['session']['metadata']['generation']['source_binding']['source_text_chars'],
            len('Context about housing in Sweden.'),
        )

    def test_generate_draft_url_only_returns_source_not_ready(self):
        # Seed previous article into the session.
        self._post(
            'ingest_source',
            {
                'source_text': 'Previous article about immigration rules.',
                'source_url': 'https://example.se/old',
                'title': 'Old',
            },
        )
        with patch(
            'content_ai.source.inspector.extract_article_from_url',
            side_effect=ArticleExtractionError(
                'Unable to extract article content from this URL.\n'
                'Paste the article text manually.'
            ),
        ):
            response = self._post(
                'generate_draft',
                {
                    'source_text': '',
                    'source_url': 'https://example.se/new',
                    'title': '',
                },
            )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertEqual(data['error']['code'], 'extraction_failed')
        self.assertIn('Unable to extract article content', data['error']['message'])

    def test_ingest_source_api_fills_text_from_url(self):
        article = ExtractedArticle(
            url='https://www.example.se/nyheter/x',
            title='Fetched title',
            text=(
                'Det är viktigt att förstå bostadsmarknaden och att följa '
                'utvecklingen i hela regionen under året.'
            ),
            domain='www.example.se',
            detected_language='sv',
            publisher='Example',
            detected_country='SE',
        )
        with patch(
            'content_ai.source.inspector.extract_article_from_url',
            return_value=article,
        ):
            response = self._post(
                'ingest_source',
                {
                    'source_url': 'https://www.example.se/nyheter/x',
                    'source_text': '',
                },
            )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertIn('bostadsmarknaden', data['session']['source_material'])
        self.assertEqual(data['session']['metadata']['source']['retrieval'], 'url_fetch')
        self.assertEqual(data['session']['metadata']['source']['title'], 'Fetched title')

    def test_set_workflow_rejects_published(self):
        self._post('set_workflow', {'state': 'approved'})
        response = self._post('set_workflow', {'state': 'published'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'validation_error')

    def test_prepare_seo_and_evaluate(self):
        self._post(
            'update_sections',
            {'sections': {'headline': 'H', 'body': 'Enough body text for metrics.'}},
        )
        seo = self._post('prepare_seo', {})
        self.assertEqual(seo.status_code, 200)
        self.assertIn('seo', seo.json())
        ev = self._post('evaluate', {})
        self.assertEqual(ev.status_code, 200)
        self.assertIn('evaluation', ev.json())

    @patch('content_ai.workspace.services.WorkspaceService.import_existing_article')
    def test_import_article_endpoint(self, mocked):
        mocked.side_effect = lambda session, post_id=None: session
        response = self._post('import_article', {'post_id': 1})
        self.assertEqual(response.status_code, 200)
        mocked.assert_called_once()

    def test_save_draft_creates_and_updates_blog_post(self):
        from blog.models import Category, Post

        Category.objects.create(name='News', slug='news')
        create = self._post(
            'save_draft',
            {
                'sections': {
                    'headline': 'Workspace Save Draft',
                    'lead': 'Lead text',
                    'body': 'Body text for the draft.',
                    'summary': 'Summary text',
                    'category': 'News',
                    'tags': ['housing', 'sweden'],
                },
            },
        )
        self.assertEqual(create.status_code, 200, create.content.decode()[:500])
        data = create.json()
        self.assertTrue(data['ok'])
        self.assertTrue(data['blog_draft']['created'])
        post_id = data['blog_draft']['post_id']
        post = Post.objects.get(pk=post_id)
        self.assertEqual(post.status, 0)
        self.assertEqual(post.title, 'Workspace Save Draft')
        self.assertIn('Lead text', post.content)
        self.assertIn('Body text', post.content)
        self.assertEqual(post.excerpt, 'Summary text')
        self.assertEqual(data['session']['linked_post_id'], post_id)

        update = self._post(
            'save_draft',
            {
                'sections': {
                    'headline': 'Workspace Save Draft Updated',
                    'lead': 'New lead',
                    'body': 'Updated body text.',
                    'summary': 'Updated summary',
                    'category': 'News',
                },
            },
        )
        self.assertEqual(update.status_code, 200)
        updated = update.json()
        self.assertFalse(updated['blog_draft']['created'])
        self.assertEqual(updated['blog_draft']['post_id'], post_id)
        self.assertEqual(
            Post.objects.filter(title__startswith='Workspace Save Draft').count(),
            1,
        )
        post.refresh_from_db()
        self.assertEqual(post.title, 'Workspace Save Draft Updated')
        self.assertIn('Updated body text', post.content)

    def test_publish_draft_then_reset_starts_clean_session(self):
        from blog.models import Category, Post

        Category.objects.create(name='News', slug='news')
        create = self._post(
            'save_draft',
            {
                'sections': {
                    'headline': 'Workspace Publish Me',
                    'lead': 'Lead text',
                    'body': 'Body text for publish.',
                    'summary': 'Summary text',
                    'category': 'News',
                },
            },
        )
        self.assertEqual(create.status_code, 200, create.content.decode()[:500])
        post_id = create.json()['blog_draft']['post_id']

        publish = self._post('publish_draft', {})
        self.assertEqual(publish.status_code, 200, publish.content.decode()[:500])
        published = publish.json()
        self.assertTrue(published['ok'])
        self.assertEqual(published['published']['status'], 'published')
        self.assertEqual(published['published']['post_id'], post_id)
        self.assertTrue(published['published']['public_url'])
        self.assertEqual(
            published['session']['publish_success']['post_id'],
            post_id,
        )
        self.assertEqual(published['session']['workflow_state'], 'published')

        post = Post.objects.get(pk=post_id)
        self.assertEqual(post.status, 1)

        reset = self._post('reset', {})
        self.assertEqual(reset.status_code, 200)
        session = reset.json()['session']
        self.assertNotEqual(session['session_id'], published['session']['session_id'])
        self.assertEqual(session['sections']['headline'], '')
        self.assertEqual(session['sections']['body'], '')
        self.assertEqual(session['source_url'], '')
        self.assertEqual(session['source_material'], '')
        self.assertFalse(session.get('linked_post_id'))
        self.assertEqual(session.get('blog_draft') or {}, {})
        self.assertEqual(session.get('publish_success') or {}, {})
        self.assertEqual(session.get('last_explanations') or [], [])
        self.assertEqual(session.get('history') or [], [])
