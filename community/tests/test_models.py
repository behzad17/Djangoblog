from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import ProtectedError
from django.test import TestCase
from django.utils import timezone

from community.constants import DiscussionStatus, ModerationReason
from community.models import CommunityCategory, Discussion, Reply

User = get_user_model()


class CommunityCategoryModelTests(TestCase):
    def test_create_category_with_required_fields(self):
        category = CommunityCategory.objects.create(
            name='مهاجرت',
            slug='مهاجرت',
        )
        self.assertEqual(category.name, 'مهاجرت')
        self.assertEqual(category.slug, 'مهاجرت')
        self.assertEqual(category.description, '')
        self.assertEqual(category.display_order, 0)
        self.assertTrue(category.is_active)
        self.assertIsNotNone(category.created_on)

    def test_str_returns_name(self):
        category = CommunityCategory.objects.create(name='مسکن', slug='مسکن')
        self.assertEqual(str(category), 'مسکن')

    def test_name_must_be_unique(self):
        CommunityCategory.objects.create(name='کار', slug='کار')
        with self.assertRaises(IntegrityError):
            CommunityCategory.objects.create(name='کار', slug='کار-2')

    def test_slug_must_be_unique(self):
        CommunityCategory.objects.create(name='کار', slug='کار')
        with self.assertRaises(IntegrityError):
            CommunityCategory.objects.create(name='شغل', slug='کار')

    def test_default_ordering(self):
        second = CommunityCategory.objects.create(
            name='B',
            slug='b',
            display_order=2,
        )
        first = CommunityCategory.objects.create(
            name='A',
            slug='a',
            display_order=1,
        )
        categories = list(CommunityCategory.objects.all())
        self.assertEqual(categories, [first, second])


class DiscussionModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='discussionauthor',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='روزمره',
            slug='روزمره',
        )
        cls.now = timezone.now()

    def _create_discussion(self, **kwargs):
        defaults = {
            'author': self.user,
            'category': self.category,
            'title': 'سؤال نمونه',
            'slug': 'سؤال-نمونه',
            'body': 'متن بحث',
            'last_activity_at': self.now,
        }
        defaults.update(kwargs)
        return Discussion.objects.create(**defaults)

    def test_create_discussion_with_required_fields(self):
        discussion = self._create_discussion()
        self.assertEqual(discussion.author, self.user)
        self.assertEqual(discussion.category, self.category)
        self.assertEqual(discussion.title, 'سؤال نمونه')
        self.assertEqual(discussion.slug, 'سؤال-نمونه')
        self.assertEqual(discussion.body, 'متن بحث')
        self.assertEqual(discussion.status, DiscussionStatus.OPEN)
        self.assertEqual(discussion.reply_count, 0)
        self.assertEqual(discussion.last_activity_at, self.now)
        self.assertFalse(discussion.is_deleted)
        self.assertIsNone(discussion.deleted_at)
        self.assertIsNone(discussion.deleted_by)
        self.assertIsNone(discussion.closed_at)
        self.assertIsNone(discussion.closed_by)
        self.assertIsNotNone(discussion.created_on)
        self.assertIsNotNone(discussion.updated_on)

    def test_str_returns_title(self):
        discussion = self._create_discussion()
        self.assertEqual(str(discussion), 'سؤال نمونه')

    def test_slug_must_be_unique(self):
        self._create_discussion()
        with self.assertRaises(IntegrityError):
            self._create_discussion(
                title='سؤال دیگر',
                slug='سؤال-نمونه',
            )

    def test_status_accepts_closed_and_hidden(self):
        closed = self._create_discussion(
            slug='closed-discussion',
            status=DiscussionStatus.CLOSED,
        )
        hidden = self._create_discussion(
            slug='hidden-discussion',
            status=DiscussionStatus.HIDDEN,
        )
        self.assertEqual(closed.status, DiscussionStatus.CLOSED)
        self.assertEqual(hidden.status, DiscussionStatus.HIDDEN)

    def test_reply_count_cannot_be_negative(self):
        discussion = self._create_discussion()
        discussion.reply_count = -1
        with self.assertRaises(ValidationError):
            discussion.full_clean()

    def test_author_related_name(self):
        discussion = self._create_discussion()
        self.assertIn(discussion, self.user.community_discussions.all())

    def test_category_related_name(self):
        discussion = self._create_discussion()
        self.assertIn(discussion, self.category.discussions.all())

    def test_author_set_null_on_user_delete(self):
        discussion = self._create_discussion()
        self.user.delete()
        discussion.refresh_from_db()
        self.assertIsNone(discussion.author_id)
        self.assertTrue(Discussion.objects.filter(pk=discussion.pk).exists())

    def test_category_protect_on_delete(self):
        self._create_discussion()
        with self.assertRaises(ProtectedError):
            self.category.delete()

    def test_closed_by_related_name(self):
        staff = User.objects.create_user(
            username='staff',
            password='password123',
        )
        discussion = self._create_discussion(
            status=DiscussionStatus.CLOSED,
            closed_by=staff,
            closed_at=self.now,
        )
        self.assertIn(discussion, staff.closed_community_discussions.all())

    def test_deleted_by_related_name(self):
        staff = User.objects.create_user(
            username='moderator',
            password='password123',
        )
        discussion = self._create_discussion(
            is_deleted=True,
            deleted_by=staff,
            deleted_at=self.now,
        )
        deleted = staff.soft_deleted_community_discussions.all()
        self.assertIn(discussion, deleted)

    def test_default_ordering_by_last_activity(self):
        older = self._create_discussion(
            slug='older',
            last_activity_at=self.now - timezone.timedelta(days=2),
        )
        newer = self._create_discussion(
            slug='newer',
            last_activity_at=self.now,
        )
        self.assertEqual(list(Discussion.objects.all()), [newer, older])


class ReplyModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='replyauthor',
            password='password123',
        )
        cls.reviewer = User.objects.create_user(
            username='reviewer',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='سلامت',
            slug='سلامت',
        )
        cls.discussion = Discussion.objects.create(
            author=cls.user,
            category=cls.category,
            title='بحث سلامت',
            slug='بحث-سلامت',
            body='متن',
            last_activity_at=timezone.now(),
        )

    def _create_reply(self, **kwargs):
        defaults = {
            'discussion': self.discussion,
            'author': self.user,
            'body': 'پاسخ نمونه',
        }
        defaults.update(kwargs)
        return Reply.objects.create(**defaults)

    def test_create_reply_with_required_fields(self):
        reply = self._create_reply()
        self.assertEqual(reply.discussion, self.discussion)
        self.assertEqual(reply.author, self.user)
        self.assertEqual(reply.body, 'پاسخ نمونه')
        self.assertFalse(reply.approved)
        self.assertIsNone(reply.moderation_reason)
        self.assertIsNone(reply.reviewed_by)
        self.assertIsNone(reply.reviewed_at)
        self.assertIsNotNone(reply.created_on)
        self.assertIsNotNone(reply.updated_on)

    def test_str_includes_author_and_discussion(self):
        reply = self._create_reply()
        self.assertIn('replyauthor', str(reply))
        self.assertIn(str(self.discussion.pk), str(reply))

    def test_str_handles_deleted_author(self):
        reply = self._create_reply(author=None)
        self.assertIn('deleted user', str(reply))

    def test_moderation_reason_choices(self):
        reply = self._create_reply(
            approved=False,
            moderation_reason=ModerationReason.NEW_USER,
        )
        self.assertEqual(reply.moderation_reason, ModerationReason.NEW_USER)

    def test_discussion_related_name(self):
        reply = self._create_reply()
        self.assertIn(reply, self.discussion.replies.all())

    def test_author_related_name(self):
        reply = self._create_reply()
        self.assertIn(reply, self.user.community_replies.all())

    def test_reviewed_by_related_name(self):
        reviewed_at = timezone.now()
        reply = self._create_reply(
            approved=True,
            reviewed_by=self.reviewer,
            reviewed_at=reviewed_at,
        )
        self.assertIn(reply, self.reviewer.reviewed_community_replies.all())
        self.assertEqual(reply.reviewed_at, reviewed_at)

    def test_author_set_null_on_user_delete(self):
        reply = self._create_reply()
        self.user.delete()
        reply.refresh_from_db()
        self.assertIsNone(reply.author_id)
        self.assertTrue(Reply.objects.filter(pk=reply.pk).exists())

    def test_cascade_delete_when_discussion_deleted(self):
        reply = self._create_reply()
        reply_id = reply.pk
        self.discussion.delete()
        self.assertFalse(Reply.objects.filter(pk=reply_id).exists())

    def test_default_ordering_is_chronological(self):
        first = self._create_reply(body='اول')
        second = self._create_reply(body='دوم')
        replies = list(Reply.objects.filter(discussion=self.discussion))
        self.assertEqual(replies, [first, second])

    def test_multiple_replies_allowed_from_same_author(self):
        self._create_reply(body='پاسخ اول')
        self._create_reply(body='پاسخ دوم')
        author_replies = self.discussion.replies.filter(author=self.user)
        self.assertEqual(author_replies.count(), 2)
