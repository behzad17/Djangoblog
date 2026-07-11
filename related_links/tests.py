from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from codestar.related.text_matching import normalize_persian_text, tokens_match
from community.models import CommunityCategory
from community.services.discussions import create_discussion
from related_links.models import RelatedLink, UsefulLinkCategory, UsefulLinkResourceType
from related_links.selectors.related import get_related_links


class RelatedLinksSelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.discussion_author = User.objects.create_user(
            username='linkdiscussionauthor',
            password='password123',
        )
        cls.community_category = CommunityCategory.objects.create(
            name='مهاجرت و اقامت',
            slug='immigration-residency',
        )
        cls.link_category, _ = UsefulLinkCategory.objects.get_or_create(
            slug='migration',
            defaults={
                'name_en': 'Migration',
                'name_fa': 'مهاجرت',
                'icon': 'bi-globe',
                'is_active': True,
            },
        )
        cls.other_link_category = UsefulLinkCategory.objects.create(
            name_en='Finance',
            name_fa='مالی',
            slug='test-finance-category',
            icon='bi-bank',
            is_active=True,
        )
        cls.resource_type, _ = UsefulLinkResourceType.objects.get_or_create(
            slug='website',
            defaults={
                'name_en': 'Website',
                'name_fa': 'وب‌سایت',
                'icon': 'bi-globe',
                'is_active': True,
            },
        )

    def setUp(self):
        RelatedLink.objects.all().delete()

    def _create_discussion(self, **kwargs):
        defaults = {
            'author': self.discussion_author,
            'category': self.community_category,
            'title': 'سؤال درباره مهاجرت',
            'body': 'به دنبال منابع مهاجرت هستم.',
        }
        defaults.update(kwargs)
        return create_discussion(**defaults)

    def _create_link(self, slug, **kwargs):
        defaults = {
            'title': f'لینک {slug}',
            'slug': slug,
            'category': self.link_category,
            'resource_type': self.resource_type,
            'url': 'https://example.com',
            'short_description': 'راهنمای مهاجرت',
            'is_active': True,
        }
        defaults.update(kwargs)
        return RelatedLink.objects.create(**defaults)

    def test_returns_mapped_category_links(self):
        discussion = self._create_discussion()
        matched = self._create_link('migration-link')
        self._create_link(
            'finance-link',
            category=self.other_link_category,
            short_description='خدمات مالی',
        )

        results = get_related_links(discussion, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matched)

    def test_excludes_inactive_links_and_categories(self):
        discussion = self._create_discussion()
        self._create_link('visible-link')
        self._create_link('inactive-link', is_active=False)
        inactive_category = UsefulLinkCategory.objects.create(
            name_en='Inactive',
            name_fa='غیرفعال',
            slug='inactive-category',
            icon='bi-x',
            is_active=False,
        )
        self._create_link(
            'inactive-category-link',
            category=inactive_category,
        )

        results = get_related_links(discussion, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].slug, 'visible-link')

    def test_limits_results_to_three(self):
        discussion = self._create_discussion()
        for index in range(5):
            self._create_link(
                f'migration-link-{index}',
                title=f'مهاجرت {index}',
            )

        results = get_related_links(discussion, limit=3)

        self.assertEqual(len(results), 3)

    def test_returns_empty_when_no_related_matches(self):
        general = CommunityCategory.objects.create(
            name='عمومی',
            slug='general',
        )
        discussion = self._create_discussion(
            title='موضوع بدون ارتباط',
            body='متن عمومی',
            category=general,
        )

        results = get_related_links(discussion, limit=3)

        self.assertEqual(results, [])

    def test_keyword_fallback_when_category_mapping_empty(self):
        buy_sell = CommunityCategory.objects.create(
            name='خرید و فروش',
            slug='buy-sell',
        )
        buy_sell_category, _ = UsefulLinkCategory.objects.get_or_create(
            slug='buy-sell',
            defaults={
                'name_en': 'Buy Sell',
                'name_fa': 'خرید و فروش',
                'icon': 'bi-cart',
                'is_active': True,
            },
        )
        discussion = self._create_discussion(
            category=buy_sell,
            title='خرید مبلمان دست دوم',
            body='به دنبال فروشنده هستم.',
        )
        matched = self._create_link(
            'furniture-link',
            category=buy_sell_category,
            title='فروش مبلمان دست دوم',
            short_description='راهنمای خرید و فروش',
        )

        results = get_related_links(discussion, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].slug, 'furniture-link')

    def test_persian_stem_keyword_match(self):
        tax_category = CommunityCategory.objects.create(
            name='عمومی مالیات',
            slug='general-tax',
        )
        discussion = self._create_discussion(
            category=tax_category,
            title='سؤال درباره مالیات بر درآمد',
            body='به دنبال منابع مالیاتی هستم.',
        )
        matched = self._create_link(
            'tax-link',
            category=self.other_link_category,
            title='راهنمای مالیاتی',
            short_description='اطلاعات مالیات',
        )

        results = get_related_links(discussion, limit=3)

        self.assertEqual(results, [matched])

    def test_get_related_links_uses_bounded_queries(self):
        discussion = self._create_discussion()
        for index in range(4):
            self._create_link(
                f'query-link-{index}',
                title=f'مهاجرت {index}',
            )

        with CaptureQueriesContext(connection) as context:
            results = get_related_links(discussion, limit=3)

        self.assertEqual(len(results), 3)
        self.assertLessEqual(len(context.captured_queries), 2)

    def test_returns_mapped_category_links_for_blog_post(self):
        from blog.models import Category, Post

        blog_category, _ = Category.objects.get_or_create(
            slug='law-integration',
            defaults={'name': 'قانون و ادغام'},
        )
        post = Post.objects.create(
            title='راهنمای اقامت',
            slug='blog-link-residency',
            author=self.discussion_author,
            category=blog_category,
            content='سؤال درباره اقامت',
            status=1,
        )
        matched = self._create_link('blog-migration-link')
        self._create_link(
            'blog-finance-link',
            category=self.other_link_category,
            short_description='خدمات مالی',
        )

        results = get_related_links(post, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matched)

    def test_get_related_links_for_blog_post_uses_bounded_queries(self):
        from blog.models import Category, Post

        blog_category, _ = Category.objects.get_or_create(
            slug='law-integration',
            defaults={'name': 'قانون و ادغام'},
        )
        post = Post.objects.create(
            title='راهنمای اقامت',
            slug='blog-link-query',
            author=self.discussion_author,
            category=blog_category,
            content='سؤال درباره اقامت',
            status=1,
        )
        for index in range(4):
            self._create_link(
                f'blog-query-link-{index}',
                title=f'مهاجرت {index}',
            )

        with CaptureQueriesContext(connection) as context:
            results = get_related_links(post, limit=3)

        self.assertEqual(len(results), 3)
        self.assertLessEqual(len(context.captured_queries), 2)

    def test_persian_normalization_for_link_matching(self):
        self.assertEqual(
            normalize_persian_text('ماليات'),
            normalize_persian_text('مالیات'),
        )
        self.assertTrue(tokens_match('مالیات', 'مالیاتی'))
