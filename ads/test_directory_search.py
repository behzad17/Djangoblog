from django.test import TestCase
from django.urls import reverse

from .models import Ad, AdCategory


class DirectorySearchTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        home = AdCategory.objects.create(slug="work-services", name="خانه و ساختمان")
        vehicles = AdCategory.objects.get(slug="vehicles-repair")
        Ad.objects.bulk_create([
            Ad(category=home, title="Fix Clean", slug="directory-fix-clean", subcategory="cleaning",
               city="Göteborg", plan="pro", is_active=True, is_approved=True,
               phone="031-21 37 00", address="Testvägen 12, Göteborg",
               target_url="https://example.com/approved", url_approved=True,
               website_url="https://example.com/unapproved"),
            Ad(category=vehicles, title="Auto City", slug="directory-auto-city", subcategory="car-repair",
               city="گوتنبرگ / Mölndal", plan="free", is_active=True, is_approved=True,
               target_url="https://example.com/auto", url_approved=True),
            Ad(category=home, title="Other Clean", slug="directory-other-clean", subcategory="cleaning",
               city="Stockholm", plan="pro", is_active=True, is_approved=True),
            Ad(category=home, title="Hidden Clean", slug="directory-hidden-clean", subcategory="cleaning",
               city="Göteborg", plan="pro", is_active=True, is_approved=False),
        ])

    def test_search_service_and_city_with_persian_spelling(self):
        response = self.client.get(reverse("ads:ads_home"), {"q": "نظافت", "city": "گوتنبرگ"})
        self.assertContains(response, "Fix Clean")
        self.assertContains(response, "مشاهده جزئیات")
        self.assertContains(response, "خانه و ساختمان · نظافت")
        self.assertNotContains(response, "Other Clean")
        self.assertNotContains(response, "Hidden Clean")
        self.assertNotContains(response, "Auto City")

    def test_city_matches_both_spellings_across_categories(self):
        response = self.client.get(reverse("ads:ads_home"), {"city": "Goteborg"})
        self.assertContains(response, "Fix Clean")
        self.assertContains(response, "Auto City")
        self.assertContains(response, "تعمیرگاه · سرویس و تعمیر خودرو")
        self.assertContains(response, "https://example.com/auto")
        free_detail = reverse("ads:ad_detail", args=["directory-auto-city"])
        self.assertNotContains(response, free_detail)
        self.assertEqual(self.client.get(free_detail).status_code, 404)

    def test_search_business_by_name(self):
        response = self.client.get(reverse("ads:ads_home"), {"q": "fix clean"})
        self.assertContains(response, "Fix Clean")
        self.assertNotContains(response, "Other Clean")

    def test_detail_contact_actions_respect_website_approval(self):
        response = self.client.get(reverse("ads:ad_detail", args=["directory-fix-clean"]))
        self.assertContains(response, 'href="tel:031213700"')
        self.assertContains(response, "مسیریابی")
        self.assertContains(response, "https://example.com/approved")
        self.assertNotContains(response, 'href="https://example.com/unapproved"')

    def test_postal_box_remains_visible_without_map_links(self):
        Ad.objects.filter(slug="directory-fix-clean").update(
            address="Box 92150, 120 08 Stockholm (آدرس پستی)",
        )
        response = self.client.get(reverse("ads:ad_detail", args=["directory-fix-clean"]))
        self.assertContains(response, "Box 92150, 120 08 Stockholm (آدرس پستی)")
        self.assertNotContains(response, "www.google.com/maps/")
        self.assertContains(response, 'href="tel:031213700"')

    def test_mixed_address_only_sends_visiting_address_to_maps(self):
        Ad.objects.filter(slug="directory-fix-clean").update(
            address="Besöksadress: Testvägen 12\n411 20 Göteborg\nPostadress: Box 92150",
        )
        response = self.client.get(reverse("ads:ad_detail", args=["directory-fix-clean"]))
        self.assertContains(response, "destination=Testv%C3%A4gen%2012%2C%20411%2020%20G%C3%B6teborg")
        self.assertNotContains(response, "destination=Bes")
        self.assertNotContains(response, "Box%2092150")
