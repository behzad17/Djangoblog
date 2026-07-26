"""Tests for Editorial AI v2 content-type registry and classification."""

from django.test import SimpleTestCase

from content_ai.editorial.content_types import (
    CONTENT_TYPE_REGISTRY,
    CONTENT_TYPES,
    EDITORIAL_GOALS,
    classify_content,
    detect_editorial_goal,
    get_profile,
    headline_lead_pass_rules,
    resolve_content_type,
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

    def test_resolve_aliases(self):
        self.assertEqual(resolve_content_type('government'), 'announcement')
        self.assertEqual(resolve_content_type('howto'), 'how_to')
        self.assertEqual(resolve_content_type('research'), 'analysis')
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


class PromptTemplateTests(SimpleTestCase):
    def test_guide_prompt_differs_from_news(self):
        news = headline_lead_pass_rules(content_type='news', goal='inform')
        guide = headline_lead_pass_rules(content_type='guide', goal='teach')
        self.assertIn('News', news)
        self.assertIn('Guide', guide)
        self.assertIn('Action-oriented', guide)
        self.assertNotEqual(news, guide)


class AssistantActionFilterTests(SimpleTestCase):
    def test_guide_actions_include_instruction_tools(self):
        actions = list_actions_for_ui('guide')
        ids = {item['id'] for item in actions}
        self.assertIn('improve_instructions', ids)
        self.assertIn('add_tips', ids)
        self.assertIn('improve_headline', ids)

    def test_news_actions_keep_core_tools(self):
        actions = list_actions_for_ui('news')
        ids = {item['id'] for item in actions}
        self.assertIn('improve_headline', ids)
        self.assertIn('rewrite_lead', ids)
        self.assertNotIn('condense_answers', ids)
