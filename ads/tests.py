from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ads.models import Ad, AdCategory, AdComment
from blog.models import UserProfile


def _pro_request_send_mail_side_effect(subject, *args, **kwargs):
    if "Pro Upgrade" in subject:
        raise Exception("SMTP failure")
    return 1


class AdsTestMixin:
    def setUp(self):
        import cloudinary

        cloudinary.config(
            cloud_name="test",
            api_key="test",
            api_secret="test",
            secure=True,
        )

        self.owner = User.objects.create_user(
            username="adowner",
            password="password123",
            email="owner@test.com",
        )
        self.other = User.objects.create_user(
            username="otheruser",
            password="password123",
            email="other@test.com",
        )
        UserProfile.objects.update_or_create(
            user=self.owner,
            defaults={"is_site_verified": True},
        )
        UserProfile.objects.update_or_create(
            user=self.other,
            defaults={"is_site_verified": True},
        )
        self.category = AdCategory.objects.create(
            name="Test Category",
            slug="test-category",
        )

    def _create_ad(self, slug, **kwargs):
        defaults = {
            "title": f"Ad {slug}",
            "slug": slug,
            "category": self.category,
            "owner": self.owner,
            "image": "test/ad-image",
            "target_url": "https://example.com",
            "city": "Tehran",
            "address": "Test address",
            "plan": "free",
            "is_active": True,
            "is_approved": True,
            "url_approved": True,
        }
        defaults.update(kwargs)
        return Ad.objects.create(**defaults)


class AdDetailAccessTests(AdsTestMixin, TestCase):
    def _detail_url(self, slug):
        return reverse("ads:ad_detail", args=[slug])

    def test_pending_free_owner_can_open_ad_detail(self):
        ad = self._create_ad("pending-free", is_approved=False, plan="free")
        self.client.login(username="adowner", password="password123")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ad.title)

    def test_approved_free_owner_can_open_ad_detail(self):
        ad = self._create_ad("approved-free", plan="free")
        self.client.login(username="adowner", password="password123")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 200)

    def test_inactive_free_owner_can_open_ad_detail(self):
        ad = self._create_ad("inactive-free", is_active=False, plan="free")
        self.client.login(username="adowner", password="password123")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 200)

    def test_public_user_gets_404_for_free_ad(self):
        ad = self._create_ad("public-free", plan="free")
        self.client.login(username="otheruser", password="password123")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 404)

    def test_pro_ad_works_for_public_user(self):
        ad = self._create_ad("public-pro", plan="pro")
        self.client.login(username="otheruser", password="password123")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 200)

    def test_public_user_gets_404_for_unapproved_pro_ad(self):
        ad = self._create_ad("hidden-pro", plan="pro", is_approved=False)
        self.client.login(username="otheruser", password="password123")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 404)

    def test_owner_can_submit_pro_request_on_pending_free_ad(self):
        ad = self._create_ad(
            "pro-request-free",
            is_approved=False,
            plan="free",
        )
        self.client.login(username="adowner", password="password123")
        response = self.client.post(
            self._detail_url(ad.slug),
            {"pro_request": "1", "phone": "0701234567"},
        )
        self.assertEqual(response.status_code, 302)
        ad.refresh_from_db()
        self.assertTrue(ad.pro_requested)
        self.assertEqual(ad.pro_request_phone, "0701234567")

    def test_expired_free_owner_can_open_ad_detail(self):
        yesterday = timezone.now().date() - timedelta(days=1)
        ad = self._create_ad(
            "expired-free",
            plan="free",
            end_date=yesterday,
        )
        self.client.login(username="adowner", password="password123")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 200)

    def test_anonymous_user_can_view_pro_ad_detail(self):
        ad = self._create_ad("anon-pro", plan="pro")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ad.title)

    def test_anonymous_user_gets_404_for_free_ad(self):
        ad = self._create_ad("anon-free", plan="free")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 404)

    def test_anonymous_post_comment_redirects_to_login(self):
        ad = self._create_ad("anon-comment-pro", plan="pro")
        response = self.client.post(
            self._detail_url(ad.slug),
            {"body": "Anonymous comment attempt"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("account_login"))

    def test_anonymous_add_to_favorites_redirects_to_login(self):
        ad = self._create_ad("anon-fav-pro", plan="pro")
        response = self.client.post(
            reverse("ads:add_ad_to_favorites", args=[ad.id]),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("account_login"), response.url)


@override_settings(
    ADMIN_EMAIL="admin@test.com",
    DEFAULT_FROM_EMAIL="noreply@test.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class EditAdSocialUrlApprovalTests(AdsTestMixin, TestCase):
    def _mock_form_save(self, ad, **field_updates):
        def save_side_effect(commit=True):
            updated = Ad.objects.get(pk=ad.pk)
            for field, value in field_updates.items():
                setattr(updated, field, value)
            if commit:
                updated.save()
            return updated

        return save_side_effect

    @patch("ads.views.AdForm")
    def test_changing_social_url_resets_social_urls_approved(self, mock_ad_form):
        ad = self._create_ad(
            "social-change",
            is_approved=False,
            social_urls_approved=True,
            instagram_url="https://instagram.com/old",
        )
        mock_form = mock_ad_form.return_value
        mock_form.is_valid.return_value = True
        mock_form.save.side_effect = self._mock_form_save(
            ad,
            instagram_url="https://instagram.com/new",
        )

        self.client.login(username="adowner", password="password123")
        response = self.client.post(reverse("ads:edit_ad", args=[ad.slug]), {})
        self.assertEqual(response.status_code, 302)
        ad.refresh_from_db()
        self.assertFalse(ad.social_urls_approved)
        self.assertEqual(ad.instagram_url, "https://instagram.com/new")

    @patch("ads.views.AdForm")
    def test_editing_unrelated_fields_does_not_reset_social_urls_approved(self, mock_ad_form):
        ad = self._create_ad(
            "social-unchanged",
            is_approved=False,
            social_urls_approved=True,
            instagram_url="https://instagram.com/same",
        )
        mock_form = mock_ad_form.return_value
        mock_form.is_valid.return_value = True
        mock_form.save.side_effect = self._mock_form_save(
            ad,
            title="Updated title only",
        )

        self.client.login(username="adowner", password="password123")
        response = self.client.post(reverse("ads:edit_ad", args=[ad.slug]), {})
        self.assertEqual(response.status_code, 302)
        ad.refresh_from_db()
        self.assertTrue(ad.social_urls_approved)
        self.assertEqual(ad.title, "Updated title only")


class DeleteAdCommentAccessTests(AdsTestMixin, TestCase):
    def _delete_comment_url(self, slug, comment_id):
        return reverse("ads:delete_ad_comment", args=[slug, comment_id])

    def test_owner_can_delete_comment_on_pending_ad(self):
        ad = self._create_ad("pending-comment", is_approved=False, plan="free")
        comment = AdComment.objects.create(
            ad=ad,
            author=self.owner,
            body="Owner comment on pending ad",
        )
        self.client.login(username="adowner", password="password123")
        response = self.client.post(
            self._delete_comment_url(ad.slug, comment.id),
        )
        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)

    def test_owner_can_delete_comment_on_inactive_ad(self):
        ad = self._create_ad("inactive-comment", is_active=False, plan="free")
        comment = AdComment.objects.create(
            ad=ad,
            author=self.owner,
            body="Owner comment on inactive ad",
        )
        self.client.login(username="adowner", password="password123")
        response = self.client.post(
            self._delete_comment_url(ad.slug, comment.id),
        )
        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertTrue(comment.is_deleted)

    def test_non_owner_gets_404_for_hidden_pro_ad(self):
        ad = self._create_ad("hidden-pro-comment", plan="pro", is_approved=False)
        comment = AdComment.objects.create(
            ad=ad,
            author=self.owner,
            body="Owner comment on hidden pro ad",
        )
        self.client.login(username="otheruser", password="password123")
        response = self.client.post(
            self._delete_comment_url(ad.slug, comment.id),
        )
        self.assertEqual(response.status_code, 404)
        comment.refresh_from_db()
        self.assertFalse(comment.is_deleted)

    def test_non_owner_cannot_delete_another_users_comment_on_visible_ad(self):
        ad = self._create_ad("visible-pro-comment", plan="pro")
        comment = AdComment.objects.create(
            ad=ad,
            author=self.owner,
            body="Owner comment on visible pro ad",
        )
        self.client.login(username="otheruser", password="password123")
        response = self.client.post(
            self._delete_comment_url(ad.slug, comment.id),
        )
        self.assertEqual(response.status_code, 302)
        comment.refresh_from_db()
        self.assertFalse(comment.is_deleted)


class AdCommentFormTests(AdsTestMixin, TestCase):
    def _detail_url(self, slug):
        return reverse("ads:ad_detail", args=[slug])

    def test_comment_form_does_not_render_visible_honeypot_label(self):
        ad = self._create_ad("comment-form-pro", plan="pro")
        self.client.login(username="adowner", password="password123")
        response = self.client.get(self._detail_url(ad.slug))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Honeypot")
        self.assertContains(response, 'name="honeypot"')
        self.assertContains(response, "ad-comment-form__honeypot")

    def test_honeypot_rejects_bot_submission(self):
        ad = self._create_ad("comment-bot-pro", plan="pro")
        self.client.login(username="adowner", password="password123")
        self.client.post(
            self._detail_url(ad.slug),
            {"body": "Valid comment", "honeypot": "spam"},
        )
        self.assertEqual(ad.comments.count(), 0)

    def test_verified_user_can_post_comment(self):
        ad = self._create_ad("comment-post-pro", plan="pro")
        self.client.login(username="adowner", password="password123")
        response = self.client.post(
            self._detail_url(ad.slug),
            {"body": "سلام، نظر تست", "honeypot": ""},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(ad.comments.filter(is_deleted=False).count(), 1)


@override_settings(
    ADMIN_EMAIL="admin@test.com",
    DEFAULT_FROM_EMAIL="noreply@test.com",
    EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
)
class ProRequestEmailTests(AdsTestMixin, TestCase):
    def _detail_url(self, slug):
        return reverse("ads:ad_detail", args=[slug])

    def test_email_sent_on_first_pro_request(self):
        ad = self._create_ad(
            "pro-email",
            is_approved=True,
            plan="free",
        )
        mail.outbox.clear()
        self.client.login(username="adowner", password="password123")
        response = self.client.post(
            self._detail_url(ad.slug),
            {"pro_request": "1", "phone": "0701234567"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 1)
        email = mail.outbox[0]
        self.assertIn(ad.title, email.subject)
        self.assertIn(str(ad.id), email.body)
        self.assertIn(self.owner.username, email.body)
        self.assertIn(self.owner.email, email.body)
        self.assertIn("0701234567", email.body)
        self.assertIn(f"/admin/ads/ad/{ad.id}/", email.body)

    def test_duplicate_pro_request_does_not_send_second_email(self):
        ad = self._create_ad(
            "pro-email-dup",
            is_approved=True,
            plan="free",
            pro_requested=True,
            pro_request_phone="0701234567",
        )
        mail.outbox.clear()
        self.client.login(username="adowner", password="password123")
        response = self.client.post(
            self._detail_url(ad.slug),
            {"pro_request": "1", "phone": "0709999999"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(mail.outbox), 0)

    @patch("ads.signals.send_mail", side_effect=_pro_request_send_mail_side_effect)
    def test_pro_request_succeeds_when_email_fails(self, mock_send_mail):
        ad = self._create_ad(
            "pro-email-fail",
            is_approved=True,
            plan="free",
        )
        self.client.login(username="adowner", password="password123")
        response = self.client.post(
            self._detail_url(ad.slug),
            {"pro_request": "1", "phone": "0701234567"},
        )
        self.assertEqual(response.status_code, 302)
        ad.refresh_from_db()
        self.assertTrue(ad.pro_requested)
        self.assertEqual(ad.pro_request_phone, "0701234567")


class RelatedAdsSelectorTests(AdsTestMixin, TestCase):
    @classmethod
    def setUpTestData(cls):
        from community.models import CommunityCategory

        cls.community_category = CommunityCategory.objects.create(
            name='سلامت',
            slug='health',
        )
        cls.health_ad_category = AdCategory.objects.create(
            name='خدمات پزشکی و سلامت',
            slug='health-welfare',
        )
        cls.other_ad_category = AdCategory.objects.create(
            name='خدمات مالی',
            slug='economi',
        )

    def setUp(self):
        super().setUp()

    def _create_discussion(self, **kwargs):
        from community.services.discussions import create_discussion

        defaults = {
            'author': self.owner,
            'category': self.community_category,
            'title': 'سؤال درباره بیمه سلامت',
            'body': 'به دنبال راهنمایی برای بیمه هستم.',
        }
        defaults.update(kwargs)
        return create_discussion(**defaults)

    def test_returns_mapped_category_ads(self):
        from ads.selectors.related import get_related_ads

        discussion = self._create_discussion()
        matched = self._create_ad(
            'health-ad',
            category=self.health_ad_category,
            plan='pro',
        )
        self._create_ad(
            'finance-ad',
            category=self.other_ad_category,
            title='خدمات مالی',
            plan='pro',
        )

        results = get_related_ads(discussion, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], matched)

    def test_excludes_pending_and_inactive_ads(self):
        from ads.selectors.related import get_related_ads

        discussion = self._create_discussion()
        self._create_ad('visible-ad', category=self.health_ad_category, plan='pro')
        self._create_ad(
            'pending-ad',
            category=self.health_ad_category,
            is_approved=False,
            plan='pro',
        )
        self._create_ad(
            'url-pending-ad',
            category=self.health_ad_category,
            url_approved=False,
            plan='pro',
        )
        self._create_ad(
            'inactive-ad',
            category=self.health_ad_category,
            is_active=False,
            plan='pro',
        )

        results = get_related_ads(discussion, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].slug, 'visible-ad')

    def test_limits_results_to_three(self):
        from ads.selectors.related import get_related_ads

        discussion = self._create_discussion()
        for index in range(5):
            self._create_ad(
                f'health-ad-{index}',
                category=self.health_ad_category,
                title=f'سلامت {index}',
                plan='pro',
            )

        results = get_related_ads(discussion, limit=3)

        self.assertEqual(len(results), 3)

    def test_returns_empty_when_no_related_matches(self):
        from ads.selectors.related import get_related_ads
        from community.models import CommunityCategory

        general = CommunityCategory.objects.create(
            name='عمومی',
            slug='general',
        )
        discussion = self._create_discussion(
            title='موضوع بدون ارتباط',
            body='متن عمومی',
            category=general,
        )

        results = get_related_ads(discussion, limit=3)

        self.assertEqual(results, [])

    def test_keyword_title_match_when_category_mapping_empty(self):
        from ads.selectors.related import get_related_ads
        from community.models import CommunityCategory

        buy_sell = CommunityCategory.objects.create(
            name='خرید و فروش',
            slug='buy-sell',
        )
        discussion = self._create_discussion(
            category=buy_sell,
            title='خرید مبلمان دست دوم',
            body='به دنبال فروشنده هستم.',
        )
        self._create_ad(
            'furniture-ad',
            category=self.other_ad_category,
            title='فروش مبلمان دست دوم',
            plan='pro',
        )

        results = get_related_ads(discussion, limit=3)

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].slug, 'furniture-ad')

    def test_excludes_free_ads(self):
        from ads.selectors.related import get_related_ads

        discussion = self._create_discussion()
        self._create_ad(
            'free-health-ad',
            category=self.health_ad_category,
            plan='free',
        )
        pro_ad = self._create_ad(
            'pro-health-ad',
            category=self.health_ad_category,
            plan='pro',
        )

        results = get_related_ads(discussion, limit=3)

        self.assertEqual(results, [pro_ad])

    def test_persian_stem_keyword_match(self):
        from ads.selectors.related import get_related_ads
        from community.models import CommunityCategory

        tax_category = CommunityCategory.objects.create(
            name='عمومی',
            slug='general-tax',
        )
        discussion = self._create_discussion(
            category=tax_category,
            title='سؤال درباره مالیات بر درآمد',
            body='به دنبال مشاور مالیاتی هستم.',
        )
        matched = self._create_ad(
            'tax-ad',
            category=self.other_ad_category,
            title='مشاوره مالیاتی برای ایرانیان',
            plan='pro',
        )

        results = get_related_ads(discussion, limit=3)

        self.assertEqual(results, [matched])

    def test_get_related_ads_uses_bounded_queries(self):
        from ads.selectors.related import get_related_ads
        from django.test.utils import CaptureQueriesContext
        from django.db import connection

        discussion = self._create_discussion()
        for index in range(4):
            self._create_ad(
                f'query-health-ad-{index}',
                category=self.health_ad_category,
                title=f'سلامت {index}',
                plan='pro',
            )

        with CaptureQueriesContext(connection) as context:
            results = get_related_ads(discussion, limit=3)

        self.assertEqual(len(results), 3)
        self.assertLessEqual(len(context.captured_queries), 2)


class PersianTextMatchingTests(TestCase):
    def test_normalizes_arabic_characters(self):
        from codestar.related.text_matching import normalize_persian_text

        self.assertEqual(
            normalize_persian_text('ماليات'),
            normalize_persian_text('مالیات'),
        )

    def test_tokens_match_persian_suffix_variants(self):
        from codestar.related.text_matching import tokens_match

        self.assertTrue(tokens_match('مالیات', 'مالیاتی'))
        self.assertTrue(tokens_match('مالیاتی', 'مالیات'))
