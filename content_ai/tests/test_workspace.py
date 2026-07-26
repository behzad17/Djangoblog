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
from content_ai.workflow.states import WorkflowState
from content_ai.workspace.actions import get_action, list_actions_for_ui
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
        self.assertIn('classification', session.metadata)
        self.assertTrue(session.content_type)

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
        )
        self.assertEqual(session.resolved_content_type(), 'guide')
        self.assertEqual(session.resolved_goal(), 'teach')
        self.assertEqual(session.template_id, 'guide.v1')
        payload = session.to_dict()
        self.assertEqual(payload['lead_label'], 'Introduction')
        self.assertEqual(payload['content_type_override'], 'guide')

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
        service.set_classification(session, content_type='guide', goal='teach')
        session.source_material = 'How to apply for support steg för steg'
        service.generate_draft(session, title='Guide')
        kwargs = editorial.generate_draft.call_args.kwargs
        self.assertEqual(kwargs['content_type'], 'guide')
        self.assertEqual(kwargs['goal'], 'teach')
        self.assertTrue(session.pipeline.get('draft_generated'))
        self.assertEqual(session.sections.headline, 'Guide title')
        self.assertEqual(session.sections.lead, 'Intro')

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


@override_settings(CONTENT_AI_PROVIDER='mock')
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
