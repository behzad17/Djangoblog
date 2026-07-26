"""Tests for configurable article length prompts."""

from django.test import SimpleTestCase

from content_ai.editorial.article_length import (
    DEFAULT_ARTICLE_LENGTH,
    article_length_prompt_block,
    resolve_article_length,
)
from content_ai.editorial.content_types import body_pass_rules, headline_lead_pass_rules
from content_ai.editorial.drafts import EditorialDraft
from content_ai.workspace.services import WorkspaceService
from unittest.mock import MagicMock


class ArticleLengthUnitTests(SimpleTestCase):
    def test_default_is_full(self):
        self.assertEqual(resolve_article_length(None), 'full')
        self.assertEqual(resolve_article_length(''), 'full')
        self.assertEqual(DEFAULT_ARTICLE_LENGTH, 'full')

    def test_aliases(self):
        self.assertEqual(resolve_article_length('Full Article'), 'full')
        self.assertEqual(resolve_article_length('news-flash'), 'news_flash')
        self.assertEqual(resolve_article_length('short'), 'brief')

    def test_full_prompt_does_not_ask_to_summarise(self):
        block = article_length_prompt_block('full')
        self.assertIn('complete Persian editorial article, not a summary', block)
        self.assertIn('professional Persian journalist', block)
        self.assertIn('Multiple well-developed body sections', block)
        self.assertIn(
            'Preserve all important facts, explanations, timelines, numbers',
            block,
        )
        self.assertIn(
            'If the source contains multiple themes or sections',
            block,
        )
        self.assertIn(
            'never invent facts or add unsupported information',
            block,
        )
        self.assertIn('Preserve all important sections of the source', block)
        self.assertIn(
            'Omit only repetition, boilerplate, advertisements, navigation',
            block,
        )
        self.assertIn(
            'Do not omit facts simply to make the article shorter',
            block,
        )
        self.assertNotIn('Write a concise Persian summary', block)

    def test_brief_prompt_is_concise(self):
        block = article_length_prompt_block('brief')
        self.assertIn('concise', block.lower())

    def test_body_rules_include_selected_length(self):
        full = body_pass_rules(
            content_type='news',
            goal='inform',
            style='journalistic',
            article_length='full',
        )
        brief = body_pass_rules(
            content_type='news',
            goal='inform',
            style='journalistic',
            article_length='brief',
        )
        self.assertIn('Full Article', full)
        self.assertIn('not a summary', full)
        self.assertIn('professional Persian journalist', full)
        self.assertIn('Brief', brief)
        self.assertNotEqual(full, brief)

    def test_headline_rules_include_length(self):
        rules = headline_lead_pass_rules(article_length='news_flash')
        self.assertIn('News Flash', rules)


class ArticleLengthServiceTests(SimpleTestCase):
    def test_generate_draft_passes_article_length(self):
        editorial = MagicMock()
        editorial.generate_draft.return_value = EditorialDraft(
            title='T',
            lead='L',
            body='B' * 200,
            summary='S',
            language='fa',
            metadata={},
        )
        service = WorkspaceService(editorial=editorial)
        session = service.new_session()
        session.source_material = 'Source article with enough text for generation.'
        session.metadata['source_binding'] = {
            'session_id': session.session_id,
            'source_url': '',
            'source_text_sha256': __import__('hashlib')
            .sha256(session.source_material.encode())
            .hexdigest(),
            'source_text_chars': len(session.source_material),
            'retrieval': 'manual_paste',
        }
        service.generate_draft(session, title='T', article_length='standard')
        kwargs = editorial.generate_draft.call_args.kwargs
        self.assertEqual(kwargs['article_length'], 'standard')
        self.assertEqual(session.article_length, 'standard')
        self.assertEqual(
            session.metadata['generation']['article_length'],
            'standard',
        )
