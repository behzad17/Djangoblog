from django.contrib.auth import get_user_model
from django.test import TestCase

from community.constants import DiscussionStatus
from community.models import CommunityCategory
from community.selectors.categories import (
    category_exists,
    get_category_by_slug,
    list_active_categories,
    list_active_categories_with_discussion_counts,
    list_categories,
)
from community.services.discussions import create_discussion

User = get_user_model()


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


class CategoryDiscussionCountSelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='categoryauthor',
            password='password123',
        )
        cls.immigration = CommunityCategory.objects.create(
            name='مهاجرت',
            slug='immigration',
            display_order=1,
        )
        cls.work = CommunityCategory.objects.create(
            name='کار و تحصیل',
            slug='work-study',
            display_order=2,
        )
        cls.inactive = CommunityCategory.objects.create(
            name='غیرفعال',
            slug='inactive',
            is_active=False,
        )
        create_discussion(
            author=cls.author,
            category=cls.immigration,
            title='بحث اول',
            body='متن',
        )
        create_discussion(
            author=cls.author,
            category=cls.immigration,
            title='بحث دوم',
            body='متن',
        )
        create_discussion(
            author=cls.author,
            category=cls.work,
            title='بحث کار',
            body='متن',
        )
        hidden = create_discussion(
            author=cls.author,
            category=cls.work,
            title='بحث مخفی',
            body='متن',
        )
        hidden.status = DiscussionStatus.HIDDEN
        hidden.save(update_fields=['status'])

    def test_list_active_categories_with_discussion_counts(self):
        categories = {
            category.slug: category.discussion_count
            for category in list_active_categories_with_discussion_counts()
        }

        self.assertEqual(categories['immigration'], 2)
        self.assertEqual(categories['work-study'], 1)
        self.assertNotIn('inactive', categories)
