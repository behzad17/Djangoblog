from django.test import TestCase

from community.models import CommunityCategory
from community.selectors.categories import (
    category_exists,
    get_category_by_slug,
    list_active_categories,
    list_categories,
)


class CategorySelectorQueryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.first = CommunityCategory.objects.create(
            name='اول',
            slug='first',
            display_order=1,
        )
        cls.second = CommunityCategory.objects.create(
            name='دوم',
            slug='second',
            display_order=2,
        )

    def test_list_categories_single_query(self):
        with self.assertNumQueries(1):
            categories = list(list_categories())
            self.assertEqual(len(categories), 2)

    def test_list_active_categories_single_query(self):
        inactive = CommunityCategory.objects.create(
            name='غیرفعال',
            slug='inactive',
            is_active=False,
        )
        with self.assertNumQueries(1):
            categories = list(list_active_categories())
            self.assertEqual(len(categories), 2)
            self.assertNotIn(inactive, categories)

    def test_get_category_by_slug_single_query(self):
        with self.assertNumQueries(1):
            category = get_category_by_slug('first')
            self.assertEqual(category, self.first)

    def test_category_exists_without_loading_model(self):
        self.assertTrue(category_exists('second'))
        self.assertFalse(category_exists('missing'))
