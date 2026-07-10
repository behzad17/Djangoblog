from django.contrib.auth import get_user_model
from django.test import TestCase

from community.constants import DiscussionStatus
from community.exceptions import (
    DiscussionDeletedError,
    InactiveCategoryError,
    InvalidDiscussionStateError,
    ValidationError,
)
from community.models import CommunityCategory
from community.services.discussions import (
    close_discussion,
    create_discussion,
    reopen_discussion,
    restore_discussion,
    soft_delete_discussion,
    update_discussion,
)

User = get_user_model()


class DiscussionServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='author',
            password='password123',
        )
        cls.staff = User.objects.create_user(
            username='staff',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='مهاجرت',
            slug='مهاجرت',
        )
        cls.inactive_category = CommunityCategory.objects.create(
            name='غیرفعال',
            slug='غیرفعال',
            is_active=False,
        )

    def test_create_discussion_happy_path(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='سؤال جدید',
            body='متن بحث',
        )
        self.assertEqual(discussion.author, self.author)
        self.assertEqual(discussion.category, self.category)
        self.assertEqual(discussion.title, 'سؤال جدید')
        self.assertEqual(discussion.body, 'متن بحث')
        self.assertEqual(discussion.status, DiscussionStatus.OPEN)
        self.assertEqual(discussion.reply_count, 0)
        self.assertFalse(discussion.is_deleted)
        self.assertTrue(discussion.slug)
        self.assertIsNotNone(discussion.last_activity_at)

    def test_create_discussion_generates_unique_slug(self):
        first = create_discussion(
            author=self.author,
            category=self.category,
            title='عنوان تکراری',
            body='متن اول',
        )
        second = create_discussion(
            author=self.author,
            category=self.category,
            title='عنوان تکراری',
            body='متن دوم',
        )
        self.assertNotEqual(first.slug, second.slug)

    def test_create_discussion_rejects_inactive_category(self):
        with self.assertRaises(InactiveCategoryError):
            create_discussion(
                author=self.author,
                category=self.inactive_category,
                title='عنوان',
                body='متن',
            )

    def test_create_discussion_rejects_empty_fields(self):
        with self.assertRaises(ValidationError):
            create_discussion(
                author=self.author,
                category=self.category,
                title='   ',
                body='متن',
            )

    def test_update_discussion_updates_fields_without_changing_slug(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='عنوان اولیه',
            body='متن اولیه',
        )
        original_slug = discussion.slug
        updated = update_discussion(
            discussion,
            title='عنوان جدید',
            body='متن جدید',
        )
        self.assertEqual(updated.slug, original_slug)
        self.assertEqual(updated.title, 'عنوان جدید')
        self.assertEqual(updated.body, 'متن جدید')

    def test_update_discussion_rejects_deleted_discussion(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='حذف شونده',
            body='متن',
        )
        soft_delete_discussion(discussion, deleted_by=self.staff)
        with self.assertRaises(DiscussionDeletedError):
            update_discussion(discussion, title='جدید')

    def test_close_discussion_sets_closed_metadata(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='بسته شونده',
            body='متن',
        )
        closed = close_discussion(discussion, closed_by=self.author)
        self.assertEqual(closed.status, DiscussionStatus.CLOSED)
        self.assertIsNotNone(closed.closed_at)
        self.assertEqual(closed.closed_by, self.author)

    def test_close_discussion_is_idempotent_when_already_closed(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='بسته',
            body='متن',
        )
        close_discussion(discussion, closed_by=self.author)
        again = close_discussion(discussion, closed_by=self.author)
        self.assertEqual(again.status, DiscussionStatus.CLOSED)

    def test_reopen_discussion_from_closed(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='بازگشایی',
            body='متن',
        )
        close_discussion(discussion, closed_by=self.author)
        reopened = reopen_discussion(discussion)
        self.assertEqual(reopened.status, DiscussionStatus.OPEN)
        self.assertIsNone(reopened.closed_at)
        self.assertIsNone(reopened.closed_by)

    def test_reopen_discussion_rejects_hidden_status(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='مخفی',
            body='متن',
        )
        discussion.status = DiscussionStatus.HIDDEN
        discussion.save(update_fields=['status'])
        with self.assertRaises(InvalidDiscussionStateError):
            reopen_discussion(discussion)

    def test_soft_delete_and_restore(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='حذف نرم',
            body='متن',
        )
        deleted = soft_delete_discussion(discussion, deleted_by=self.staff)
        self.assertTrue(deleted.is_deleted)
        self.assertIsNotNone(deleted.deleted_at)
        self.assertEqual(deleted.deleted_by, self.staff)

        restored = restore_discussion(deleted)
        self.assertFalse(restored.is_deleted)
        self.assertIsNone(restored.deleted_at)
        self.assertIsNone(restored.deleted_by)

    def test_soft_delete_rejects_already_deleted(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='حذف دوباره',
            body='متن',
        )
        soft_delete_discussion(discussion, deleted_by=self.staff)
        with self.assertRaises(InvalidDiscussionStateError):
            soft_delete_discussion(discussion, deleted_by=self.staff)

    def test_restore_rejects_active_discussion(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='فعال',
            body='متن',
        )
        with self.assertRaises(InvalidDiscussionStateError):
            restore_discussion(discussion)
