from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from ads.homepage_pro_ads import (
    HOMEPAGE_PRO_ROTATION_SECONDS,
    get_homepage_pro_ads,
)
from ads.tests import AdsTestMixin


class GetHomepageProAdsTests(AdsTestMixin, TestCase):
    def _create_pro_ad(self, slug, **kwargs):
        return self._create_ad(slug, plan="pro", **kwargs)

    def test_returns_empty_when_no_visible_pro_ads(self):
        self.assertEqual(get_homepage_pro_ads(), [])

    def test_returns_all_pro_ads_when_six_or_fewer(self):
        ads = [
            self._create_pro_ad(f"pro-{index}", title=f"Pro {index}")
            for index in range(6)
        ]
        result = get_homepage_pro_ads()
        self.assertEqual(len(result), 6)
        self.assertEqual([ad.id for ad in result], [ad.id for ad in reversed(ads)])

    def test_returns_all_when_fewer_than_six(self):
        ad = self._create_pro_ad("only-pro", title="Only Pro")
        result = get_homepage_pro_ads()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, ad.id)

    def test_excludes_inactive_and_non_pro_ads(self):
        self._create_pro_ad("visible-pro")
        self._create_pro_ad("inactive-pro", is_active=False)
        self._create_ad("free-ad", plan="free")
        result = get_homepage_pro_ads()
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].slug, "visible-pro")

    def test_more_than_six_returns_three_newest_plus_three_rotating(self):
        created = []
        base_time = timezone.now()
        for index in range(8):
            ad = self._create_pro_ad(f"pro-{index}", title=f"Pro {index}")
            Ad = ad.__class__
            Ad.objects.filter(pk=ad.pk).update(
                created_on=base_time - timedelta(hours=index)
            )
            ad.refresh_from_db()
            created.append(ad)

        ordered = sorted(created, key=lambda item: item.created_on, reverse=True)
        result = get_homepage_pro_ads()
        self.assertEqual(len(result), 6)
        self.assertEqual(
            [ad.id for ad in result[:3]],
            [ad.id for ad in ordered[:3]],
        )
        rotating_ids = {ad.id for ad in result[3:]}
        remaining_ids = {ad.id for ad in ordered[3:]}
        self.assertEqual(len(rotating_ids), 3)
        self.assertTrue(rotating_ids.issubset(remaining_ids))

    def test_rotation_is_stable_within_bucket(self):
        for index in range(7):
            self._create_pro_ad(f"pro-{index}")

        first = [ad.id for ad in get_homepage_pro_ads()]
        second = [ad.id for ad in get_homepage_pro_ads()]
        self.assertEqual(first, second)

    def test_rotation_changes_after_bucket(self):
        for index in range(7):
            self._create_pro_ad(f"pro-{index}")

        base_time = timezone.now()
        with patch("ads.homepage_pro_ads.timezone.now") as mock_now:
            mock_now.return_value = base_time
            first = [ad.id for ad in get_homepage_pro_ads()]

            mock_now.return_value = base_time + timedelta(
                seconds=HOMEPAGE_PRO_ROTATION_SECONDS + 1
            )
            second = [ad.id for ad in get_homepage_pro_ads()]

        self.assertEqual(len(first), 6)
        self.assertEqual(len(second), 6)
        self.assertEqual(first[:3], second[:3])
        self.assertNotEqual(first[3:], second[3:])


class HomepageProAdsTemplateTests(AdsTestMixin, TestCase):
    def test_homepage_renders_section_when_pro_ads_exist(self):
        self._create_ad("homepage-pro", plan="pro", title="Homepage Pro Ad")
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="homepage-pro-ads-section"', count=2)
        self.assertContains(response, "Homepage Pro Ad")
        self.assertContains(response, 'class="homepage-pro-card"', count=2)

    def test_homepage_hides_section_when_no_pro_ads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "homepage-pro-ads-section")

    def test_mobile_and_desktop_placements_both_present(self):
        self._create_ad("placement-pro", plan="pro", title="Placement Pro")
        response = self.client.get(reverse("home"))
        content = response.content.decode()
        self.assertEqual(content.count('class="homepage-pro-ads-section"'), 2)
        self.assertIn('class="d-md-none"', content)
        self.assertIn('class="d-none d-md-block"', content)
