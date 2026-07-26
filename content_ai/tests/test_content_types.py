"""Tests for Editorial Intelligence v1 — content types, goals, styles."""

from django.test import SimpleTestCase

from content_ai.editorial.content_types import (
    CONTENT_TYPE_REGISTRY,
    CONTENT_TYPES,
    EDITORIAL_GOALS,
    WRITING_STYLES,
    classify_content,
    detect_editorial_goal,
    detect_writing_style,
    get_profile,
    headline_lead_pass_rules,
    resolve_content_type,
    resolve_style,
)
from content_ai.workspace.actions import list_actions_for_ui


class ContentTypeRegistryTests(SimpleTestCase):
    def test_all_content_types_registered(self):
        for content_type in CONTENT_TYPES:
            self.assertIn(content_type, CONTENT_TYPE_REGISTRY)
            profile = get_profile(content_type)
            self.assertTrue(profile.lead_label)
            self.assertTrue(profile.headline_strategy)
            self.assertTrue(profile.body_structure)
            self.assertTrue(profile.assistant_action_ids)
            self.assertTrue(profile.default_style)

    def test_new_v1_types_registered(self):
        for key in ('event', 'review', 'community_story'):
            self.assertIn(key, CONTENT_TYPE_REGISTRY)

    def test_resolve_aliases(self):
        self.assertEqual(resolve_content_type('government'), 'announcement')
        self.assertEqual(resolve_content_type('howto'), 'how_to')
        self.assertEqual(resolve_content_type('research'), 'analysis')
        self.assertEqual(resolve_content_type('community'), 'community_story')
        self.assertEqual(resolve_content_type('unknown-xyz'), 'news')


class ClassifierTests(SimpleTestCase):
    def test_guide_classification(self):
        result = classify_content(
            title='Guide: How to apply for housing',
            text='This guide explains steg för steg how to apply.',
            url='https://example.se/guide/bostad',
        )
        self.assertEqual(result.content_type, 'guide')
        self.assertGreater(result.confidence, 0.5)
        self.assertTrue(result.reasons)

    def test_press_release_classification(self):
        result = classify_content(
            title='Pressmeddelande från myndigheten',
            text='Idag meddelar organisationen ett press release.',
            url='https://example.se/press/nytt',
        )
        self.assertIn(result.content_type, {'press_release', 'announcement'})

    def test_event_classification(self):
        result = classify_content(
            title='Community festival event',
            text='Join the evenemang and workshop this Saturday.',
            url='https://example.se/event/festival',
        )
        self.assertEqual(result.content_type, 'event')

    def test_override_wins(self):
        result = classify_content(
            title='Guide',
            text='guide how to',
            override='interview',
        )
        self.assertEqual(result.content_type, 'interview')
        self.assertEqual(result.confidence, 1.0)

    def test_default_news_when_no_signals(self):
        result = classify_content(title='Something', text='Plain text without cues.')
        self.assertEqual(result.content_type, 'news')


class GoalDetectionTests(SimpleTestCase):
    def test_teach_goal_for_guide(self):
        result = detect_editorial_goal(
            content_type='guide',
            title='How to register',
            text='Learn the steps to complete registration.',
        )
        self.assertEqual(result.goal, 'teach')

    def test_document_goal_exists(self):
        self.assertIn('document', EDITORIAL_GOALS)

    def test_goal_override(self):
        result = detect_editorial_goal(
            content_type='news',
            override='warn',
        )
        self.assertEqual(result.goal, 'warn')
        self.assertEqual(result.confidence, 1.0)

    def test_all_goals_exist(self):
        self.assertIn('inform', EDITORIAL_GOALS)
        self.assertIn('explain', EDITORIAL_GOALS)


class StyleDetectionTests(SimpleTestCase):
    def test_guide_defaults_to_educational(self):
        result = detect_writing_style(
            content_type='guide',
            title='Housing guide',
            text='Step by step instructions.',
        )
        self.assertEqual(result.style, 'educational')
        self.assertGreater(result.confidence, 0.4)

    def test_style_override(self):
        result = detect_writing_style(
            content_type='news',
            override='analytical',
        )
        self.assertEqual(result.style, 'analytical')
        self.assertEqual(result.confidence, 1.0)

    def test_resolve_style_aliases(self):
        self.assertEqual(resolve_style('edu', content_type='news'), 'educational')
        self.assertEqual(
            resolve_style(None, content_type='analysis'),
            'analytical',
        )

    def test_all_styles_exist(self):
        self.assertIn('journalistic', WRITING_STYLES)
        self.assertIn('human_interest', WRITING_STYLES)


class PromptTemplateTests(SimpleTestCase):
    def test_guide_prompt_differs_from_news(self):
        news = headline_lead_pass_rules(
            content_type='news',
            goal='inform',
            style='journalistic',
        )
        guide = headline_lead_pass_rules(
            content_type='guide',
            goal='teach',
            style='educational',
        )
        self.assertIn('News', news)
        self.assertIn('Guide', guide)
        self.assertIn('Action-oriented', guide)
        self.assertIn('Writing style: Educational', guide)
        self.assertNotEqual(news, guide)


class AssistantActionFilterTests(SimpleTestCase):
    def test_guide_actions_include_instruction_tools(self):
        actions = list_actions_for_ui('guide')
        ids = {item['id'] for item in actions}
        self.assertIn('improve_instructions', ids)
        self.assertIn('simplify_instructions', ids)
        self.assertIn('add_warning', ids)
        self.assertIn('improve_structure', ids)

    def test_news_actions_keep_core_tools(self):
        actions = list_actions_for_ui('news')
        ids = {item['id'] for item in actions}
        self.assertIn('improve_headline', ids)
        self.assertIn('rewrite_lead', ids)
        self.assertIn('make_neutral', ids)
        self.assertNotIn('condense_answers', ids)

    def test_analysis_actions(self):
        ids = {item['id'] for item in list_actions_for_ui('analysis')}
        self.assertIn('strengthen_argument', ids)
        self.assertIn('neutralise_tone', ids)
        self.assertIn('improve_clarity', ids)

    def test_interview_actions(self):
        ids = {item['id'] for item in list_actions_for_ui('interview')}
        self.assertIn('improve_introduction', ids)
        self.assertIn('condense_answers', ids)
        self.assertIn('improve_flow', ids)
