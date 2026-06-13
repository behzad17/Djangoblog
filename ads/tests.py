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
