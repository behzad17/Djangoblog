import cloudinary
from django.contrib.auth.models import User
from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext

from askme.models import Moderator
from community.models import CommunityCategory
from community.services.discussions import create_discussion
from experts.selectors.related import get_related_experts


class RelatedExpertsSelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
            secure=True,
        )

        cls.discussion_author = User.objects.create_user(
            username='expertdiscussionauthor',
            password='password123',
        )
        cls.community_category = CommunityCategory.objects.create(
            name='حقوق و قوانین',
            slug='law-legal',
        )

    def setUp(self):
        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
            secure=True,
        )
        Moderator.objects.all().delete()

    def _create_discussion(self, **kwargs):
        defaults = {
            'author': self.discussion_author,
            'category': self.community_category,
            'title': 'سؤال حقوقی',
            'body': 'نیاز به مشاور حقوقی دارم.',
        }
        defaults.update(kwargs)
        return create_discussion(**defaults)

    def _create_expert(self, slug, **kwargs):
        user = User.objects.create_user(
            username=f'expert-user-{slug}',
            password='password123',
        )
        defaults = {
            'user': user,
            'expert_title': 'وکیل مهاجرت',
            'complete_name': f'متخصص {slug}',
            'field_specialty': 'حقوق و مهاجرت',
            'bio': 'مشاوره حقوقی',
            'slug': slug,
            'profile_image': 'test/expert-image',
            'is_active': True,
        }
        defaults.update(kwargs)
        return Moderator.objects.create(**defaults)

    def test_returns_mapped_category_experts(self):
        discussion = self._create_discussion()
        matched = self._create_expert('legal-expert')
        self._create_expert(
            'finance-expert',
            expert_title='حسابدار',
            field_specialty='مالی',
            bio='خدمات مالیاتی',
        )

        results = get_related_experts(discussion, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matched)

    def test_excludes_inactive_experts(self):
        discussion = self._create_discussion()
        self._create_expert('visible-expert')
        self._create_expert(
            'inactive-expert',
            is_active=False,
        )
        self._create_expert(
            'incomplete-profile-expert',
            complete_name='نام متخصص',
            profile_image='placeholder',
        )

        results = get_related_experts(discussion, limit=3)
        slugs = {expert.slug for expert in results}

        self.assertIn('visible-expert', slugs)
        self.assertIn('incomplete-profile-expert', slugs)
        self.assertNotIn('inactive-expert', slugs)

    def test_limits_results_to_three(self):
        discussion = self._create_discussion()
        for index in range(5):
            self._create_expert(
                f'legal-expert-{index}',
                expert_title=f'وکیل {index}',
            )

        results = get_related_experts(discussion, limit=3)

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

        results = get_related_experts(discussion, limit=3)

        self.assertEqual(results, [])

    def test_keyword_fallback_when_category_mapping_empty(self):
        buy_sell = CommunityCategory.objects.create(
            name='خرید و فروش',
            slug='buy-sell',
        )
        discussion = self._create_discussion(
            category=buy_sell,
            title='خرید مبلمان دست دوم',
            body='به دنبال فروشنده هستم.',
        )
        matched = self._create_expert(
            'furniture-expert',
            expert_title='فروش مبلمان',
            field_specialty='خرید و فروش',
        )

        results = get_related_experts(discussion, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matched)

    def test_persian_stem_keyword_match(self):
        tax_category = CommunityCategory.objects.create(
            name='عمومی مالیات',
            slug='general-tax',
        )
        discussion = self._create_discussion(
            category=tax_category,
            title='سؤال درباره مالیات بر درآمد',
            body='به دنبال مشاور مالیاتی هستم.',
        )
        matched = self._create_expert(
            'tax-expert',
            expert_title='مشاور مالیاتی',
            field_specialty='مالی',
        )

        results = get_related_experts(discussion, limit=3)

        self.assertEqual(results, [matched])

    def test_prefers_topical_keywords_over_loosely_related_experts(self):
        discussion = self._create_discussion(
            title='شرکت حسابداری',
            body='دنبال شرکت حسابداری هستم.',
        )
        accountant = self._create_expert(
            'accountant-expert',
            expert_title='حسابدار',
            field_specialty='مالی و حسابداری',
            bio='خدمات حسابداری و مالیاتی',
        )
        self._create_expert(
            'immigration-expert',
            expert_title='وکیل مهاجرت',
            field_specialty='حقوق و مهاجرت',
            bio='مشاوره حقوقی',
        )
        self._create_expert(
            'family-law-expert',
            expert_title='وکیل خانواده',
            field_specialty='حقوق خانواده',
            bio='دعاوی خانواده',
        )

        results = get_related_experts(discussion, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].slug, 'accountant-expert')

    def test_does_not_pad_results_with_weak_matches(self):
        discussion = self._create_discussion(
            title='شرکت حسابداری',
            body='دنبال شرکت حسابداری هستم.',
        )
        self._create_expert(
            'accountant-only',
            expert_title='حسابدار',
            field_specialty='مالی و حسابداری',
        )
        self._create_expert(
            'unrelated-lawyer',
            expert_title='وکیل مهاجرت',
            field_specialty='حقوق و مهاجرت',
        )

        results = get_related_experts(discussion, limit=3)

        self.assertEqual(len(results), 1)

    def test_specific_category_fallback_when_no_keywords(self):
        immigration = CommunityCategory.objects.create(
            name='مهاجرت',
            slug='immigration-residency',
        )
        discussion = self._create_discussion(
            category=immigration,
            title='و در به',
            body='با برای از',
        )
        matched = self._create_expert(
            'fallback-migration-expert',
            expert_title='وکیل مهاجرت',
            field_specialty='مهاجرت و اقامت',
        )
        self._create_expert(
            'fallback-family-lawyer',
            expert_title='وکیل خانواده',
            field_specialty='حقوق خانواده',
        )

        results = get_related_experts(discussion, limit=3)

        self.assertEqual(results, [matched])

    def test_no_fallback_for_broad_category_without_keywords(self):
        discussion = self._create_discussion(
            title='و در به',
            body='با برای از',
        )
        self._create_expert('broad-legal-expert')

        results = get_related_experts(discussion, limit=3)

        self.assertEqual(results, [])

    def test_get_related_experts_uses_bounded_queries(self):
        discussion = self._create_discussion()
        for index in range(4):
            self._create_expert(
                f'query-expert-{index}',
                expert_title=f'وکیل {index}',
            )

        with CaptureQueriesContext(connection) as context:
            results = get_related_experts(discussion, limit=3)

        self.assertEqual(len(results), 3)
        self.assertLessEqual(len(context.captured_queries), 2)

    def test_returns_mapped_category_experts_for_blog_post(self):
        from blog.models import Category, Post

        blog_category, _ = Category.objects.get_or_create(
            slug='law-integration',
            defaults={'name': 'قانون و ادغام'},
        )
        post = Post.objects.create(
            title='راهنمای اقامت',
            slug='blog-expert-residency',
            author=self.discussion_author,
            category=blog_category,
            content='سؤال درباره اقامت',
            status=1,
        )
        matched = self._create_expert(
            'blog-legal-expert',
            field_specialty='مهاجرت و اقامت',
        )
        self._create_expert(
            'blog-finance-expert',
            expert_title='حسابدار',
            field_specialty='مالی',
        )

        results = get_related_experts(post, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matched)

    def test_get_related_experts_for_blog_post_uses_bounded_queries(self):
        from blog.models import Category, Post

        blog_category, _ = Category.objects.get_or_create(
            slug='law-integration',
            defaults={'name': 'قانون و ادغام'},
        )
        post = Post.objects.create(
            title='راهنمای اقامت',
            slug='blog-expert-query',
            author=self.discussion_author,
            category=blog_category,
            content='سؤال درباره مهاجرت و اقامت',
            status=1,
        )
        for index in range(4):
            self._create_expert(
                f'blog-query-expert-{index}',
                expert_title=f'وکیل مهاجرت {index}',
                field_specialty='مهاجرت و اقامت',
            )

        with CaptureQueriesContext(connection) as context:
            results = get_related_experts(post, limit=3)

        self.assertEqual(len(results), 3)
        self.assertLessEqual(len(context.captured_queries), 2)
