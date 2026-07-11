from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from blog.models import UserProfile
from community.constants import DiscussionStatus
from community.forms import ReplyCreateForm
from community.models import CommunityCategory, Discussion, Reply
from community.services.discussions import create_discussion
from notifications.constants import NotificationType
from notifications.models import Notification

User = get_user_model()


class CommunityViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='author',
            password='password123',
        )
        cls.replier = User.objects.create_user(
            username='replier',
            password='password123',
        )
        cls.other_user = User.objects.create_user(
            username='other',
            password='password123',
        )
        for user in (cls.author, cls.replier, cls.other_user):
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'is_site_verified': True},
            )

        cls.category = CommunityCategory.objects.create(
            name='مهاجرت',
            slug='immigration',
        )
        cls.discussion = create_discussion(
            author=cls.author,
            category=cls.category,
            title='سؤال درباره مهاجرت',
            body='به دنبال مشاور مهاجرت هستم.',
        )

    def _align_discussion_for_migration_expert(self):
        self.category.slug = 'immigration-residency'
        self.category.save(update_fields=['slug'])
        self.discussion.title = 'سؤال درباره مهاجرت'
        self.discussion.body = 'به دنبال مشاور مهاجرت هستم.'
        self.discussion.save(update_fields=['title', 'body'])

    def test_community_home_redirects_to_discussion_list(self):
        response = self.client.get(reverse('community:home'))
        self.assertRedirects(response, reverse('community:discussion_list'))

    def test_discussion_list_renders(self):
        response = self.client.get(reverse('community:discussion_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'گفتگو، تجربه و همفکری')
        self.assertContains(response, 'ایجاد بحث جدید')
        self.assertContains(response, 'جستجو در انجمن')
        self.assertContains(response, self.discussion.title)

    def test_discussion_list_hero_includes_purpose_copy(self):
        response = self.client.get(reverse('community:discussion_list'))
        self.assertContains(
            response,
            'گفتگو، تجربه و همفکری',
        )
        self.assertContains(
            response,
            'بخش گفتگوها فضایی برای گفتگو و تبادل نظر میان ایرانیان ساکن سوئد است.',
        )

    def test_discussion_list_renders_stats_bar(self):
        response = self.client.get(reverse('community:discussion_list'))
        self.assertContains(response, 'community-home-stats')
        self.assertContains(response, 'عضو فعال')
        self.assertContains(response, 'دسته‌بندی')
        self.assertContains(response, 'پاسخ')
        self.assertContains(response, 'بحث')
        self.assertEqual(response.context['community_home_stats']['total_discussions'], 1)

    def test_discussion_list_shows_category_discussion_counts(self):
        response = self.client.get(reverse('community:discussion_list'))
        self.assertContains(response, 'community-category-nav')
        self.assertContains(response, f'{self.category.name}')
        self.assertContains(response, '1 بحث')

    def test_discussion_list_card_shows_metadata(self):
        response = self.client.get(reverse('community:discussion_list'))
        self.assertContains(response, 'community-discussion-card__footer')
        self.assertContains(response, 'community-discussion-card__preview')
        self.assertContains(response, self.author.username)
        self.assertContains(response, '0 پاسخ')
        self.assertNotContains(response, 'community-discussion-card__badge--status-open')

    def test_discussion_list_shows_section_headings(self):
        response = self.client.get(reverse('community:discussion_list'))
        self.assertContains(response, 'موضوعات')
        self.assertContains(response, 'نمایش')
        self.assertContains(response, 'بحث‌های اخیر')
        self.assertContains(response, 'community-list-section--discussions')

    def test_discussion_list_shows_search_guidance_panel(self):
        response = self.client.get(reverse('community:discussion_list'))
        self.assertContains(response, 'community-search-guidance')
        self.assertContains(
            response,
            'قبل از ایجاد بحث جدید، ابتدا در انجمن جستجو کنید.',
        )
        self.assertContains(
            response,
            'ممکن است پاسخ سؤال شما قبلاً توسط دیگران داده شده باشد.',
        )
        self.assertContains(response, 'جستجو در انجمن')

    def test_discussion_list_hides_search_guidance_when_query_present(self):
        response = self.client.get(
            reverse('community:discussion_list'),
            {'q': 'مهاجرت'},
        )
        self.assertNotContains(response, 'community-search-guidance')
        self.assertNotContains(
            response,
            'قبل از ایجاد بحث جدید، ابتدا در انجمن جستجو کنید.',
        )

    def test_discussion_detail_renders(self):
        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.discussion.title)
        self.assertContains(response, 'به دنبال مشاور مهاجرت هستم.')
        self.assertIsInstance(response.context['reply_form'], ReplyCreateForm)
        self.assertEqual(response.context['related_ads'], [])
        self.assertEqual(response.context['related_experts'], [])
        self.assertEqual(response.context['related_useful_links'], [])

    def _create_useful_link(self, slug, **kwargs):
        from related_links.models import (
            RelatedLink,
            UsefulLinkCategory,
            UsefulLinkResourceType,
        )

        category = kwargs.pop('category', None) or UsefulLinkCategory.objects.create(
            name_en='Migration',
            name_fa='مهاجرت',
            slug=f'migration-{slug}',
            icon='bi-globe',
            is_active=True,
        )
        resource_type = kwargs.pop('resource_type', None) or UsefulLinkResourceType.objects.create(
            name_en='Website',
            name_fa='وب‌سایت',
            slug=f'website-{slug}',
            icon='bi-globe',
            is_active=True,
        )
        defaults = {
            'title': f'لینک {slug}',
            'slug': slug,
            'category': category,
            'resource_type': resource_type,
            'url': 'https://example.com',
            'short_description': 'راهنمای مهاجرت',
            'is_active': True,
        }
        defaults.update(kwargs)
        return RelatedLink.objects.create(**defaults)

    def test_discussion_detail_renders_related_ads(self):
        import cloudinary
        from ads.models import Ad, AdCategory

        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
            secure=True,
        )
        ad_category = AdCategory.objects.create(
            name='خدمات حقوقی',
            slug='legal-financial',
        )
        Ad.objects.create(
            title='مشاور حقوقی',
            slug='legal-ad',
            category=ad_category,
            owner=self.author,
            image='test/ad-image',
            target_url='https://example.com',
            city='Stockholm',
            plan='pro',
            is_active=True,
            is_approved=True,
            url_approved=True,
        )
        self.category.slug = 'immigration-residency'
        self.category.save(update_fields=['slug'])

        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'آگهی‌های مرتبط')
        self.assertContains(response, 'مشاور حقوقی')
        self.assertEqual(len(response.context['related_ads']), 1)

    def test_discussion_detail_renders_related_experts_only(self):
        import cloudinary
        from askme.models import Moderator

        self._align_discussion_for_migration_expert()
        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
            secure=True,
        )
        expert_user = User.objects.create_user(
            username='relatedexpert',
            password='password123',
        )
        Moderator.objects.create(
            user=expert_user,
            expert_title='وکیل مهاجرت',
            complete_name='متخصص حقوقی',
            field_specialty='مهاجرت و اقامت',
            slug='related-expert',
            profile_image='test/expert-image',
            is_active=True,
        )
        self.category.slug = 'immigration-residency'
        self.category.save(update_fields=['slug'])

        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'آگهی‌های مرتبط')
        self.assertContains(response, 'متخصصان مرتبط')
        self.assertContains(response, 'متخصص حقوقی')
        self.assertEqual(response.context['related_ads'], [])
        self.assertEqual(len(response.context['related_experts']), 1)

    def test_discussion_detail_renders_related_ads_and_experts(self):
        import cloudinary
        from ads.models import Ad, AdCategory
        from askme.models import Moderator

        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
            secure=True,
        )
        ad_category = AdCategory.objects.create(
            name='خدمات حقوقی',
            slug='legal-financial',
        )
        Ad.objects.create(
            title='مشاور حقوقی',
            slug='legal-ad-both',
            category=ad_category,
            owner=self.author,
            image='test/ad-image',
            target_url='https://example.com',
            city='Stockholm',
            plan='pro',
            is_active=True,
            is_approved=True,
            url_approved=True,
        )
        expert_user = User.objects.create_user(
            username='relatedexpertboth',
            password='password123',
        )
        Moderator.objects.create(
            user=expert_user,
            expert_title='وکیل مهاجرت',
            complete_name='متخصص حقوقی',
            field_specialty='مهاجرت و اقامت',
            slug='related-expert-both',
            profile_image='test/expert-image',
            is_active=True,
        )
        self.category.slug = 'immigration-residency'
        self.category.save(update_fields=['slug'])

        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'آگهی‌های مرتبط')
        self.assertContains(response, 'متخصصان مرتبط')
        self.assertEqual(len(response.context['related_ads']), 1)
        self.assertEqual(len(response.context['related_experts']), 1)

    def test_discussion_detail_renders_no_related_sections(self):
        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'آگهی‌های مرتبط')
        self.assertNotContains(response, 'متخصصان مرتبط')
        self.assertNotContains(response, 'لینک‌های مفید مرتبط')
        self.assertEqual(response.context['related_ads'], [])
        self.assertEqual(response.context['related_experts'], [])
        self.assertEqual(response.context['related_useful_links'], [])

    def test_discussion_detail_renders_related_useful_links_only(self):
        from related_links.models import UsefulLinkCategory

        UsefulLinkCategory.objects.filter(slug='migration').delete()
        migration_category = UsefulLinkCategory.objects.create(
            name_en='Migration',
            name_fa='مهاجرت',
            slug='migration',
            icon='bi-globe',
            is_active=True,
        )
        self._create_useful_link(
            'migration-link-only',
            category=migration_category,
            title='راهنمای مهاجرت',
        )
        self.category.slug = 'immigration-residency'
        self.category.save(update_fields=['slug'])

        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'آگهی‌های مرتبط')
        self.assertNotContains(response, 'متخصصان مرتبط')
        self.assertContains(response, 'لینک‌های مفید مرتبط')
        self.assertContains(response, 'راهنمای مهاجرت')
        self.assertEqual(len(response.context['related_useful_links']), 1)

    def test_discussion_detail_renders_related_ads_and_links(self):
        import cloudinary
        from ads.models import Ad, AdCategory
        from related_links.models import UsefulLinkCategory

        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
            secure=True,
        )
        ad_category = AdCategory.objects.create(
            name='خدمات حقوقی',
            slug='legal-financial',
        )
        Ad.objects.create(
            title='مشاور حقوقی',
            slug='legal-ad-links',
            category=ad_category,
            owner=self.author,
            image='test/ad-image',
            target_url='https://example.com',
            city='Stockholm',
            plan='pro',
            is_active=True,
            is_approved=True,
            url_approved=True,
        )
        UsefulLinkCategory.objects.filter(slug='migration').delete()
        migration_category = UsefulLinkCategory.objects.create(
            name_en='Migration',
            name_fa='مهاجرت',
            slug='migration',
            icon='bi-globe',
            is_active=True,
        )
        self._create_useful_link(
            'migration-link-ads',
            category=migration_category,
            title='راهنمای مهاجرت',
        )
        self.category.slug = 'immigration-residency'
        self.category.save(update_fields=['slug'])

        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'آگهی‌های مرتبط')
        self.assertNotContains(response, 'متخصصان مرتبط')
        self.assertContains(response, 'لینک‌های مفید مرتبط')
        self.assertEqual(len(response.context['related_ads']), 1)
        self.assertEqual(len(response.context['related_useful_links']), 1)

    def test_discussion_detail_renders_related_experts_and_links(self):
        import cloudinary
        from askme.models import Moderator
        from related_links.models import UsefulLinkCategory

        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
            secure=True,
        )
        expert_user = User.objects.create_user(
            username='relatedexpertlinks',
            password='password123',
        )
        Moderator.objects.create(
            user=expert_user,
            expert_title='وکیل مهاجرت',
            complete_name='متخصص حقوقی',
            field_specialty='مهاجرت و اقامت',
            slug='related-expert-links',
            profile_image='test/expert-image',
            is_active=True,
        )
        UsefulLinkCategory.objects.filter(slug='migration').delete()
        migration_category = UsefulLinkCategory.objects.create(
            name_en='Migration',
            name_fa='مهاجرت',
            slug='migration',
            icon='bi-globe',
            is_active=True,
        )
        self._create_useful_link(
            'migration-link-experts',
            category=migration_category,
            title='راهنمای مهاجرت',
        )
        self.category.slug = 'immigration-residency'
        self.category.save(update_fields=['slug'])

        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'آگهی‌های مرتبط')
        self.assertContains(response, 'متخصصان مرتبط')
        self.assertContains(response, 'لینک‌های مفید مرتبط')
        self.assertEqual(len(response.context['related_experts']), 1)
        self.assertEqual(len(response.context['related_useful_links']), 1)

    def test_discussion_detail_renders_all_related_sections(self):
        import cloudinary
        from ads.models import Ad, AdCategory
        from askme.models import Moderator
        from related_links.models import UsefulLinkCategory

        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
            secure=True,
        )
        ad_category = AdCategory.objects.create(
            name='خدمات حقوقی',
            slug='legal-financial',
        )
        Ad.objects.create(
            title='مشاور حقوقی',
            slug='legal-ad-all',
            category=ad_category,
            owner=self.author,
            image='test/ad-image',
            target_url='https://example.com',
            city='Stockholm',
            plan='pro',
            is_active=True,
            is_approved=True,
            url_approved=True,
        )
        expert_user = User.objects.create_user(
            username='relatedexpertall',
            password='password123',
        )
        Moderator.objects.create(
            user=expert_user,
            expert_title='وکیل مهاجرت',
            complete_name='متخصص حقوقی',
            field_specialty='مهاجرت و اقامت',
            slug='related-expert-all',
            profile_image='test/expert-image',
            is_active=True,
        )
        UsefulLinkCategory.objects.filter(slug='migration').delete()
        migration_category = UsefulLinkCategory.objects.create(
            name_en='Migration',
            name_fa='مهاجرت',
            slug='migration',
            icon='bi-globe',
            is_active=True,
        )
        self._create_useful_link(
            'migration-link-all',
            category=migration_category,
            title='راهنمای مهاجرت',
        )
        self.category.slug = 'immigration-residency'
        self.category.save(update_fields=['slug'])

        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'آگهی‌های مرتبط')
        self.assertContains(response, 'متخصصان مرتبط')
        self.assertContains(response, 'لینک‌های مفید مرتبط')
        self.assertEqual(len(response.context['related_ads']), 1)
        self.assertEqual(len(response.context['related_experts']), 1)
        self.assertEqual(len(response.context['related_useful_links']), 1)

    def test_discussion_create_requires_login(self):
        response = self.client.get(reverse('community:discussion_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_discussion_create_post(self):
        self.client.login(username='author', password='password123')
        response = self.client.post(
            reverse('community:discussion_create'),
            {
                'category': self.category.pk,
                'title': 'بحث جدید',
                'body': 'متن بحث جدید',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        discussion = Discussion.objects.get(title='بحث جدید')
        self.assertEqual(discussion.author, self.author)
        self.assertContains(response, 'بحث شما با موفقیت ایجاد شد.')

    def test_discussion_reply_post(self):
        self.client.login(username='replier', password='password123')
        response = self.client.post(
            reverse('community:discussion_reply', args=[self.discussion.slug]),
            {'body': 'این یک پاسخ تست است.'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        reply = Reply.objects.get(discussion=self.discussion, author=self.replier)
        self.assertEqual(reply.body, 'این یک پاسخ تست است.')

    def test_discussion_close_by_author(self):
        self.client.login(username='author', password='password123')
        response = self.client.post(
            reverse('community:discussion_close', args=[self.discussion.slug]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.discussion.refresh_from_db()
        self.assertEqual(self.discussion.status, DiscussionStatus.CLOSED)
        self.assertContains(response, 'بحث بسته شد')

    def test_closed_discussion_rejects_reply(self):
        self.discussion.status = DiscussionStatus.CLOSED
        self.discussion.save(update_fields=['status'])
        self.client.login(username='replier', password='password123')
        response = self.client.post(
            reverse('community:discussion_reply', args=[self.discussion.slug]),
            {'body': 'پاسخ بعد از بسته شدن'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Reply.objects.filter(
                discussion=self.discussion,
                body='پاسخ بعد از بسته شدن',
            ).exists(),
        )
        self.assertContains(response, 'امکان ثبت پاسخ')

    def test_community_search_renders(self):
        response = self.client.get(
            reverse('community:search'),
            {'q': 'مهاجرت'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.discussion.title)
        self.assertNotContains(response, 'community-search-guidance')

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=0)
    def test_approved_reply_notifies_discussion_author(self):
        self.client.login(username='replier', password='password123')
        self.client.post(
            reverse('community:discussion_reply', args=[self.discussion.slug]),
            {'body': 'پاسخ با اعلان'},
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.author,
                notification_type=NotificationType.COMMUNITY_REPLY,
            ).exists(),
        )

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=0)
    def test_self_reply_does_not_notify(self):
        self.client.login(username='author', password='password123')
        self.client.post(
            reverse('community:discussion_reply', args=[self.discussion.slug]),
            {'body': 'پاسخ خودم'},
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.author,
                notification_type=NotificationType.COMMUNITY_REPLY,
            ).exists(),
        )

    def test_anonymous_user_sees_create_discussion_cta_to_login(self):
        response = self.client.get(reverse('community:discussion_list'))
        self.assertContains(response, 'بحث جدید')
        self.assertContains(response, reverse('account_login'))

    def test_unverified_user_sees_create_discussion_cta_to_complete_setup(self):
        unverified = User.objects.create_user(
            username='unverified',
            password='password123',
        )
        UserProfile.objects.update_or_create(
            user=unverified,
            defaults={'is_site_verified': False},
        )
        self.client.login(username='unverified', password='password123')
        response = self.client.get(reverse('community:discussion_list'))
        self.assertContains(response, 'بحث جدید')
        self.assertContains(response, reverse('complete_setup'))

    def test_verified_user_sees_create_discussion_cta_to_create_page(self):
        self.client.login(username='author', password='password123')
        response = self.client.get(reverse('community:discussion_list'))
        self.assertContains(response, 'بحث جدید')
        self.assertContains(response, reverse('community:discussion_create'))

    def test_unverified_user_sees_verification_prompt_on_open_discussion(self):
        unverified = User.objects.create_user(
            username='unverified-detail',
            password='password123',
        )
        UserProfile.objects.update_or_create(
            user=unverified,
            defaults={'is_site_verified': False},
        )
        self.client.login(username='unverified-detail', password='password123')
        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )
        self.assertContains(
            response,
            'برای ارسال سؤال یا پاسخ، ابتدا حساب کاربری خود را تکمیل و تأیید کنید.',
        )
        self.assertContains(response, reverse('complete_setup'))
        self.assertNotContains(response, 'ثبت پاسخ')

    def test_closed_discussion_does_not_show_verification_prompt(self):
        unverified = User.objects.create_user(
            username='unverified-closed',
            password='password123',
        )
        UserProfile.objects.update_or_create(
            user=unverified,
            defaults={'is_site_verified': False},
        )
        self.discussion.status = DiscussionStatus.CLOSED
        self.discussion.save(update_fields=['status'])
        self.client.login(username='unverified-closed', password='password123')
        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )
        self.assertNotContains(
            response,
            'برای ارسال سؤال یا پاسخ، ابتدا حساب کاربری خود را تکمیل و تأیید کنید.',
        )
        self.assertNotContains(response, 'ثبت پاسخ')
