from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings

from community.constants import DiscussionStatus, ModerationReason
from community.exceptions import (
    DiscussionClosedError,
    DiscussionDeletedError,
    InvalidDiscussionStateError,
    ReplyModerationError,
    UnauthorizedAuthorError,
    ValidationError,
)
from community.models import CommunityCategory
from community.services.discussions import (
    close_discussion,
    create_discussion,
    soft_delete_discussion,
)
from community.services.replies import (
    approve_reply,
    create_reply,
    edit_reply,
    reject_reply,
)

User = get_user_model()


class ReplyServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='discussionauthor',
            password='password123',
        )
        cls.other = User.objects.create_user(
            username='otheruser',
            password='password123',
        )
        cls.reviewer = User.objects.create_user(
            username='reviewer',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='آموزش',
            slug='آموزش',
        )

    def _create_open_discussion(self, **kwargs):
        defaults = {
            'author': self.author,
            'category': self.category,
            'title': 'بحث باز',
            'body': 'متن بحث',
        }
        defaults.update(kwargs)
        return create_discussion(**defaults)

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=0)
    def test_create_reply_auto_approved_updates_counters(self):
        discussion = self._create_open_discussion()
        reply = create_reply(
            discussion=discussion,
            author=self.other,
            body='پاسخ مفید',
        )
        discussion.refresh_from_db()
        self.assertTrue(reply.approved)
        self.assertEqual(discussion.reply_count, 1)
        self.assertEqual(discussion.last_activity_at, reply.created_on)

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=5)
    def test_create_reply_pending_does_not_update_counters(self):
        discussion = self._create_open_discussion()
        reply = create_reply(
            discussion=discussion,
            author=self.other,
            body='پاسخ جدید',
        )
        discussion.refresh_from_db()
        self.assertFalse(reply.approved)
        self.assertEqual(reply.moderation_reason, ModerationReason.NEW_USER)
        self.assertEqual(discussion.reply_count, 0)

    def test_create_reply_rejects_closed_discussion(self):
        discussion = self._create_open_discussion()
        close_discussion(discussion, closed_by=self.author)
        with self.assertRaises(DiscussionClosedError):
            create_reply(
                discussion=discussion,
                author=self.other,
                body='دیر شده',
            )

    def test_create_reply_rejects_deleted_discussion(self):
        discussion = self._create_open_discussion()
        soft_delete_discussion(discussion, deleted_by=self.reviewer)
        with self.assertRaises(DiscussionDeletedError):
            create_reply(
                discussion=discussion,
                author=self.other,
                body='حذف شده',
            )

    def test_create_reply_rejects_hidden_discussion(self):
        discussion = self._create_open_discussion()
        discussion.status = DiscussionStatus.HIDDEN
        discussion.save(update_fields=['status'])
        with self.assertRaises(InvalidDiscussionStateError):
            create_reply(
                discussion=discussion,
                author=self.other,
                body='مخفی',
            )

    def test_create_reply_requires_authenticated_author(self):
        discussion = self._create_open_discussion()
        with self.assertRaises(ValidationError):
            create_reply(discussion=discussion, author=None, body='بدون کاربر')

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=0)
    def test_edit_reply_by_author(self):
        discussion = self._create_open_discussion()
        reply = create_reply(
            discussion=discussion,
            author=self.other,
            body='اولیه',
        )
        updated = edit_reply(reply=reply, author=self.other, body='ویرایش شده')
        self.assertEqual(updated.body, 'ویرایش شده')

    def test_edit_reply_rejects_non_author(self):
        discussion = self._create_open_discussion()
        reply = create_reply(
            discussion=discussion,
            author=self.other,
            body='اولیه',
        )
        with self.assertRaises(UnauthorizedAuthorError):
            edit_reply(reply=reply, author=self.author, body='نقض')

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=0)
    def test_edit_reply_with_link_removes_approval_and_updates_counters(self):
        discussion = self._create_open_discussion()
        reply = create_reply(
            discussion=discussion,
            author=self.other,
            body='پاسخ تایید شده',
        )
        discussion.refresh_from_db()
        self.assertEqual(discussion.reply_count, 1)

        edit_reply(
            reply=reply,
            author=self.other,
            body='لینک https://example.com',
        )
        reply.refresh_from_db()
        discussion.refresh_from_db()
        self.assertFalse(reply.approved)
        self.assertEqual(
            reply.moderation_reason,
            ModerationReason.CONTAINS_LINK,
        )
        self.assertEqual(discussion.reply_count, 0)

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=5)
    def test_approve_reply_updates_counters(self):
        discussion = self._create_open_discussion()
        reply = create_reply(
            discussion=discussion,
            author=self.other,
            body='در انتظار',
        )
        approved = approve_reply(reply=reply, reviewer=self.reviewer)
        discussion.refresh_from_db()
        self.assertTrue(approved.approved)
        self.assertEqual(approved.reviewed_by, self.reviewer)
        self.assertIsNotNone(approved.reviewed_at)
        self.assertEqual(discussion.reply_count, 1)

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=0)
    def test_reject_reply_updates_counters(self):
        discussion = self._create_open_discussion()
        reply = create_reply(
            discussion=discussion,
            author=self.other,
            body='تایید شده',
        )
        discussion.refresh_from_db()
        self.assertEqual(discussion.reply_count, 1)

        reject_reply(reply=reply, reviewer=self.reviewer)
        discussion.refresh_from_db()
        self.assertEqual(discussion.reply_count, 0)

    def test_reject_reply_rejects_invalid_reason(self):
        discussion = self._create_open_discussion()
        reply = create_reply(
            discussion=discussion,
            author=self.other,
            body='متن',
        )
        with self.assertRaises(ReplyModerationError):
            reject_reply(
                reply=reply,
                reviewer=self.reviewer,
                reason='invalid-reason',
            )

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=0)
    def test_approve_reply_is_idempotent(self):
        discussion = self._create_open_discussion()
        reply = create_reply(
            discussion=discussion,
            author=self.other,
            body='پاسخ',
        )
        first = approve_reply(reply=reply, reviewer=self.reviewer)
        second = approve_reply(reply=first, reviewer=self.reviewer)
        discussion.refresh_from_db()
        self.assertEqual(discussion.reply_count, 1)
        self.assertTrue(second.approved)
