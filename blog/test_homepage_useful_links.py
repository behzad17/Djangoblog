from django.test import TestCase
from django.urls import reverse

from related_links.models import UsefulLinkCategory


class HomepageUsefulLinksTests(TestCase):
    def setUp(self):
        UsefulLinkCategory.objects.all().update(is_active=False)
        self.categories = [
            UsefulLinkCategory.objects.create(
                name_en=f"Topic {index}", name_fa=f"موضوع {index}",
                slug=f"homepage-topic-{index}", icon="bi-bank",
                display_order=17 - index,
            )
            for index in range(18)
        ]

    def test_all_active_categories_follow_directory_order(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            [category.pk for category in response.context["homepage_useful_link_categories"]],
            [category.pk for category in reversed(self.categories)],
        )
        for category in self.categories:
            self.assertContains(response, f'href="/related-links/?category={category.slug}"', count=2)

    def test_mobile_and_desktop_placements(self):
        response = self.client.get(reverse("home"))
        html = response.content.decode()
        self.assertContains(response, 'class="homepage-useful-links__card"', count=36)
        desktop = html.index('id="homepage-useful-links-desktop-heading"')
        latest = html.index('id="category-latest-posts-heading"')
        self.assertLess(latest, desktop)
        self.assertLess(desktop, html.index('ad-placeholder-category-section', desktop))
        mobile = html.index('id="homepage-useful-links-mobile-heading"')
        self.assertLess(mobile, html.index('class="mobile-homepage-banners"', mobile))
        self.assertLess(mobile, html.index('class="popular-posts-sidebar"', mobile))

    def test_inactive_categories_do_not_appear(self):
        self.categories[0].is_active = False
        self.categories[0].save()
        response = self.client.get(reverse("home"))
        self.assertNotContains(response, f'href="/related-links/?category={self.categories[0].slug}"')
        self.assertEqual(len(response.context["homepage_useful_link_categories"]), 17)
