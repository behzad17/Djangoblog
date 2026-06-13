from datetime import timedelta

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ads.models import Ad, AdCategory


class AdDetailAccessTests(TestCase):
    def setUp(self):
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
            "plan": "free",
            "is_active": True,
            "is_approved": True,
            "url_approved": True,
        }
        defaults.update(kwargs)
        return Ad.objects.create(**defaults)

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
