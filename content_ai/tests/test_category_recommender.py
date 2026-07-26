"""Tests for intelligent Blog category recommendation."""

from django.test import SimpleTestCase, TestCase

from blog.models import Category
from content_ai.editorial.category_recommender import recommend_category
from content_ai.workspace.services import WorkspaceService


SAMPLE_CATEGORIES = [
    {'slug': 'platform-updates', 'name': 'تازه‌های روز', 'description': ''},
    {'slug': 'careers-economy', 'name': 'اقتصاد و بازار کار', 'description': ''},
    {'slug': 'life-in-sweden', 'name': 'زندگی در سوئد', 'description': ''},
    {'slug': 'law-integration', 'name': 'قانون و ادغام', 'description': ''},
    {'slug': 'skills-learning', 'name': 'آموزش و مهارت', 'description': ''},
    {'slug': 'events-announcements', 'name': 'رویدادها و اطلاعیه‌ها', 'description': ''},
    {'slug': 'public-services', 'name': 'خدمات عمومی', 'description': ''},
]


class CategoryRecommenderUnitTests(SimpleTestCase):
    def test_tax_article_prefers_economy(self):
        body = (
            'Skatteverket reminds residents to complete their tax declaration. '
            'The deklaration deadline affects salary and inkomst reporting. '
            'Economists say the arbetsmarknad remains stable.'
        )
        result = recommend_category(
            headline='Tax declaration reminder from Skatteverket',
            source_title='Skatteverket press',
            body=body,
            content_type='announcement',
            goal='inform',
            publisher='Skatteverket',
            categories=SAMPLE_CATEGORIES,
        )
        self.assertIsNotNone(result.selected)
        self.assertEqual(result.selected.slug, 'careers-economy')
        self.assertGreaterEqual(result.selected.confidence, 0.7)
        self.assertGreaterEqual(len(result.candidates), 1)
        self.assertLessEqual(len(result.candidates), 3)
        self.assertTrue(result.entities)
        self.assertTrue(result.reasons)

    def test_housing_guide_prefers_life_in_sweden(self):
        body = (
            'This guide explains how to find bostad in Sverige. '
            'You need personnummer and BankID before signing a lease. '
            'Living costs and försäkring are important for everyday life.'
        )
        result = recommend_category(
            headline='Guide: housing in Sweden',
            body=body,
            content_type='guide',
            goal='teach',
            categories=SAMPLE_CATEGORIES,
        )
        self.assertEqual(result.selected.slug, 'life-in-sweden')

    def test_weak_match_falls_back_to_general_news(self):
        result = recommend_category(
            headline='Hello',
            body='Short unrelated text without topical cues xyz.',
            content_type='other',
            categories=SAMPLE_CATEGORIES,
        )
        self.assertTrue(result.weak_match)
        self.assertEqual(result.selected.slug, 'platform-updates')
        self.assertIn('No strong category match', result.message)
        self.assertLess(result.selected.confidence, 0.9)

    def test_never_classifies_from_url_alone(self):
        result = recommend_category(
            headline='',
            source_title='',
            body='',
            categories=SAMPLE_CATEGORIES,
        )
        self.assertTrue(result.weak_match)
        self.assertIn('No strong category match', result.message)

    def test_auto_select_message_when_confident(self):
        body = (
            'Skatteverket tax deklaration inkomst ekonomi jobb arbetsmarknad '
            'salary lön اقتصاد مالیات بازار کار employment market update '
            'from the Swedish tax agency about declarations.'
        )
        result = recommend_category(
            headline='Skatteverket tax declaration',
            body=body,
            content_type='news',
            publisher='Skatteverket',
            categories=SAMPLE_CATEGORIES,
        )
        self.assertEqual(result.selected.slug, 'careers-economy')
        if result.selected.confidence >= 0.90:
            self.assertTrue(result.auto_selected)
            self.assertIn('Auto-selected', result.message)
        else:
            self.assertIn('review', result.message.lower())

    def test_new_category_supported_via_name_without_hardcoded_id(self):
        categories = SAMPLE_CATEGORIES + [
            {
                'slug': 'climate-environment',
                'name': 'Climate & Environment',
                'description': 'climate environment sustainability miljö',
            }
        ]
        result = recommend_category(
            headline='Climate policy update',
            body=(
                'New climate environment sustainability rules affect miljö '
                'policy across municipalities this year.'
            ),
            content_type='news',
            categories=categories,
        )
        self.assertEqual(result.selected.slug, 'climate-environment')


class CategoryRecommendationWorkspaceTests(TestCase):
    def setUp(self):
        for item in SAMPLE_CATEGORIES:
            Category.objects.get_or_create(
                slug=item['slug'],
                defaults={'name': item['name']},
            )

    def test_ingest_stores_category_recommendation(self):
        service = WorkspaceService()
        session = service.new_session()
        service.ingest_source(
            session,
            title='Skatteverket tax reminder',
            text=(
                'Skatteverket asks residents to file their tax deklaration. '
                'The economy and arbetsmarknad context is important for salary.'
            ),
            publisher='Skatteverket',
        )
        rec = session.metadata.get('category_recommendation') or {}
        self.assertTrue(rec.get('selected'))
        self.assertEqual(rec['selected']['slug'], 'careers-economy')
        self.assertTrue(session.sections.category)
        payload = session.to_dict()
        self.assertIn('category_recommendation', payload)
        self.assertEqual(
            payload['category_recommendation']['selected']['slug'],
            'careers-economy',
        )
