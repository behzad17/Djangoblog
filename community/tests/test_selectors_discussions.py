from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from community.constants import DiscussionStatus
from community.models import CommunityCategory, Discussion
from community.selectors.categories import (
    category_exists,
    get_category_by_slug,
    list_active_categories,
    list_categories,
)
from community.services.discussions import create_discussion, soft_delete_discussion

User = get_user_model()


class CategorySelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.active = CommunityCategory.objects.create(
            name='فعال',
            slug='فعال',
            display_order=2,
        )
        cls.inactive = CommunityCategory.objects.create(
            name='غیرفعال',
            slug='غیرفعال',
            display_order=1,
            is_active=False,
        )

    def test_list_categories_orders_by_display_order_then_name(self):
        categories = list(list_categories())
        self.assertEqual(categories, [self.inactive, self.active])

    def test_list_active_categories_hides_inactive(self):
        categories = list(list_active_categories())
        self.assertEqual(categories, [self.active])

    def test_get_category_by_slug_returns_active_category(self):
        category = get_category_by_slug('فعال')
        self.assertEqual(category, self.active)

    def test_get_category_by_slug_excludes_inactive(self):
        from community.models import CommunityCategory as CategoryModel

        with self.assertRaises(CategoryModel.DoesNotExist):
            get_category_by_slug('غیرفعال')

    def test_category_exists_checks_all_categories(self):
        self.assertTrue(category_exists('غیرفعال'))
        self.assertFalse(category_exists('missing'))


class DiscussionSelectorVisibilityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='selectorauthor',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='انتخابگر',
            slug='selector-category',
        )

    def _create(self, **kwargs):
        defaults = {
            'author': self.author,
            'category': self.category,
            'title': kwargs.pop('title', 'بحث'),
            'body': 'متن',
        }
        defaults.update(kwargs)
        return create_discussion(**defaults)

    def test_public_selectors_hide_deleted_discussions(self):
        from community.selectors.discussions import list_discussions

        visible = self._create(title='قابل مشاهده', body='متن')
        deleted = self._create(title='حذف شده', body='متن')
        soft_delete_discussion(deleted, deleted_by=self.author)

        slugs = set(list_discussions().values_list('slug', flat=True))
        self.assertIn(visible.slug, slugs)
        self.assertNotIn(deleted.slug, slugs)

    def test_public_selectors_hide_hidden_discussions(self):
        from community.selectors.discussions import list_discussions

        visible = self._create(title='باز', body='متن')
        hidden = self._create(title='مخفی', body='متن')
        hidden.status = DiscussionStatus.HIDDEN
        hidden.save(update_fields=['status'])

        slugs = set(list_discussions().values_list('slug', flat=True))
        self.assertIn(visible.slug, slugs)
        self.assertNotIn(hidden.slug, slugs)

    def test_list_pending_discussions(self):
        from community.selectors.discussions import list_pending_discussions

        visible = self._create(title='باز', body='متن')
        hidden = self._create(title='مخفی', body='متن')
        hidden.status = DiscussionStatus.HIDDEN
        hidden.save(update_fields=['status'])
        deleted = self._create(title='حذف شده', body='متن')
        deleted.status = DiscussionStatus.HIDDEN
        deleted.save(update_fields=['status'])
        soft_delete_discussion(deleted, deleted_by=self.author)

        results = list(list_pending_discussions())
        self.assertEqual(results, [hidden])
        self.assertNotIn(visible, results)
        self.assertNotIn(deleted, results)


class DiscussionSelectorBehaviorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='discussionselector',
            password='password123',
        )
        cls.other = User.objects.create_user(
            username='otherselector',
            password='password123',
        )
        cls.category_a = CommunityCategory.objects.create(
            name='دسته A',
            slug='category-a',
        )
        cls.category_b = CommunityCategory.objects.create(
            name='دسته B',
            slug='category-b',
        )

    def setUp(self):
        self.open_recent = create_discussion(
            author=self.author,
            category=self.category_a,
            title='باز جدید',
            body='متن',
        )
        Discussion.objects.filter(pk=self.open_recent.pk).update(
            last_activity_at=timezone.now(),
        )
        self.open_recent.refresh_from_db()

        self.closed = create_discussion(
            author=self.other,
            category=self.category_a,
            title='بسته',
            body='متن',
        )
        self.closed.status = DiscussionStatus.CLOSED
        self.closed.last_activity_at = timezone.now() - timezone.timedelta(hours=1)
        self.closed.save(update_fields=['status', 'last_activity_at'])

        self.older = create_discussion(
            author=self.author,
            category=self.category_b,
            title='قدیمی',
            body='متن',
        )
        Discussion.objects.filter(pk=self.older.pk).update(
            created_on=timezone.now() - timezone.timedelta(days=3),
            last_activity_at=timezone.now() - timezone.timedelta(days=2),
        )
        self.older.refresh_from_db()

    def test_list_discussions_orders_by_last_activity(self):
        from community.selectors.discussions import list_discussions

        results = list(list_discussions())
        self.assertEqual(results[0], self.open_recent)
        self.assertEqual(results[1], self.closed)
        self.assertEqual(results[2], self.older)

    def test_list_latest_discussions_orders_by_created_on(self):
        from community.selectors.discussions import list_latest_discussions

        results = list(list_latest_discussions())
        self.assertEqual(results[-1], self.older)

    def test_list_open_and_closed_filters(self):
        from community.selectors.discussions import (
            list_closed_discussions,
            list_open_discussions,
        )

        open_slugs = set(list_open_discussions().values_list('slug', flat=True))
        closed_slugs = set(
            list_closed_discussions().values_list('slug', flat=True)
        )
        self.assertIn(self.open_recent.slug, open_slugs)
        self.assertIn(self.older.slug, open_slugs)
        self.assertIn(self.closed.slug, closed_slugs)
        self.assertNotIn(self.closed.slug, open_slugs)

    def test_list_discussions_by_category(self):
        from community.selectors.discussions import list_discussions_by_category

        results = list(list_discussions_by_category(self.category_a))
        slugs = {discussion.slug for discussion in results}
        self.assertEqual(slugs, {self.open_recent.slug, self.closed.slug})

    def test_get_discussion_by_slug(self):
        from community.selectors.discussions import get_discussion_by_slug

        discussion = get_discussion_by_slug(self.open_recent.slug)
        self.assertEqual(discussion, self.open_recent)

    def test_list_discussions_by_author(self):
        from community.selectors.discussions import list_discussions_by_author

        results = list(list_discussions_by_author(self.author))
        slugs = {discussion.slug for discussion in results}
        self.assertEqual(slugs, {self.open_recent.slug, self.older.slug})

    def test_discussion_exists(self):
        from community.selectors.discussions import discussion_exists

        self.assertTrue(discussion_exists(self.open_recent.slug))
        self.assertFalse(discussion_exists('missing-slug'))

    def test_list_discussions_uses_select_related(self):
        from community.selectors.discussions import list_discussions

        with self.assertNumQueries(1):
            discussions = list(list_discussions())
            for discussion in discussions:
                _ = discussion.category.name
                if discussion.author_id:
                    _ = discussion.author.username
