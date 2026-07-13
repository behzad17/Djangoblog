from datetime import timedelta
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ads.models import Ad, AdCategory
from blog.models import Category, Post, UserProfile
from notifications.weekly_digest import (
    build_weekly_digest_email_context,
    build_weekly_digest_featured_items,
    build_weekly_digest_stats,
    build_weekly_digest_summary_lines,
    get_weekly_digest_period,
)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@test.com',
)
class WeeklyDigestContentTests(TestCase):
    def setUp(self):
        Site.objects.update_or_create(
            pk=settings.SITE_ID,
            defaults={'domain': 'testserver', 'name': 'Peyvand'},
        )
        self.category = Category.objects.create(name='News', slug='news')
        self.events_category = Category.objects.create(
            name='Events',
            slug='events-announcements',
        )
        self.community_author = User.objects.create_user(
            username='community',
            email='community@test.com',
            password='password123',
        )
        self.editor = User.objects.create_user(
            username='editor',
            email='editor@test.com',
            password='password123',
        )
        profile, _ = UserProfile.objects.get_or_create(user=self.editor)
        profile.can_publish_without_approval = True
        profile.save(update_fields=['can_publish_without_approval'])
        self.ad_category = AdCategory.objects.create(name='Biz', slug='biz')

    def test_stats_exclude_questions_and_zero_summary_lines(self):
        Post.objects.create(
            title='Community Article',
            slug='community-article',
            author=self.community_author,
            content='Body',
            status=1,
            category=self.category,
        )
        period_end = timezone.localdate()
        period_start = period_end - timedelta(days=7)
        stats = build_weekly_digest_stats(period_start, period_end)
        summary_lines = build_weekly_digest_summary_lines(stats)

        self.assertEqual(stats['new_articles'], 1)
        self.assertEqual(stats['new_events'], 0)
        self.assertNotIn('new_questions', stats)
        self.assertEqual(len(summary_lines), 1)
        self.assertEqual(summary_lines[0]['text'], '1 مقاله جدید')

    def test_featured_items_prioritize_editorial_then_events(self):
        Post.objects.create(
            title='Editorial One',
            slug='editorial-one',
            author=self.editor,
            content='Editorial body',
            excerpt='Editorial excerpt',
            status=1,
            category=self.category,
        )
        Post.objects.create(
            title='Community Article',
            slug='community-article',
            author=self.community_author,
            content='Community body',
            status=1,
            category=self.category,
        )
        Post.objects.create(
            title='Event One',
            slug='event-one',
            author=self.community_author,
            content='Event body',
            excerpt='Event excerpt',
            status=1,
            category=self.events_category,
            event_location='استکهلم',
        )

        period_end = timezone.localdate()
        period_start = period_end - timedelta(days=7)
        featured_items = build_weekly_digest_featured_items(period_start, period_end)

        self.assertEqual(len(featured_items), 2)
        self.assertEqual(featured_items[0]['title'], 'Editorial One')
        self.assertEqual(featured_items[1]['title'], 'Event One')

    def test_email_context_uses_weekly_page_cta(self):
        Post.objects.create(
            title='Article One',
            slug='article-one',
            author=self.community_author,
            content='Body',
            status=1,
            category=self.category,
        )
        Post.objects.create(
            title='Article Two',
            slug='article-two',
            author=self.community_author,
            content='Body',
            status=1,
            category=self.category,
        )

        period_start, period_end = get_weekly_digest_period()
        context = build_weekly_digest_email_context(period_start, period_end)

        self.assertEqual(context['cta_text'], 'مشاهده همه 2 مقاله')
        self.assertIn('/this-week/', context['cta_url'])
        self.assertNotIn('new_questions', context)

    def test_email_context_falls_back_to_generic_cta_without_articles(self):
        Ad.objects.create(
            title='Business',
            slug='business-ad',
            category=self.ad_category,
            owner=self.community_author,
            image='test/ad',
            target_url='https://example.com',
            is_approved=True,
            is_active=True,
            url_approved=True,
        )

        period_start, period_end = get_weekly_digest_period()
        context = build_weekly_digest_email_context(period_start, period_end)

        self.assertEqual(context['cta_text'], 'مشاهده همه تازه‌های این هفته')

    @patch('blog.views.build_weekly_digest_page_context')
    def test_weekly_highlights_page_renders(self, mock_page_context):
        mock_page_context.return_value = {
            'summary_lines': [{'emoji': '📰', 'text': '1 مقاله جدید'}],
            'featured_items': [],
            'articles': [],
            'events': [],
            'businesses': [],
            'pro_ads': [],
            'new_articles': 1,
            'new_events': 0,
            'new_businesses': 0,
            'new_pro_ads': 0,
            'period_start': timezone.localdate() - timedelta(days=7),
            'period_end': timezone.localdate(),
        }

        response = self.client.get(reverse('weekly_highlights'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'تازه‌های این هفته')
