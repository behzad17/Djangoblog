from django.test import TestCase
from django.urls import reverse

from ads.models import AdCategory
from related_links.models import UsefulLinkCategory


class HomepageBusinessCategoriesTests(TestCase):
    def test_directory_order_links_and_homepage_placements(self):
        category = AdCategory.objects.create(
            name='خدمت تازه', slug='new-homepage-service', display_order=100,
        )
        UsefulLinkCategory.objects.create(
            name_en='Reference', name_fa='مرجع', slug='homepage-reference',
            icon='bi-bank',
        )
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            list(response.context['homepage_business_categories']),
            list(AdCategory.objects.order_by('display_order', 'name')),
        )
        self.assertContains(
            response, f'href="{reverse("ads:ads_by_category", args=[category.slug])}"',
            count=2,
        )
        html = response.content.decode()
        for device in ('mobile', 'desktop'):
            useful = html.index(f'id="homepage-useful-links-{device}-heading"')
            business = html.index(f'id="homepage-business-categories-{device}-heading"')
            self.assertLess(useful, business)

    def test_empty_directory_omits_section(self):
        AdCategory.objects.all().delete()
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'homepage-business-categories__card')
        self.assertNotContains(response, 'id="homepage-business-categories-mobile-heading"')
