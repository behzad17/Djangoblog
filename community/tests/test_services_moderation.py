from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.utils import timezone

from community.constants import ModerationReason
from community.models import CommunityCategory, Discussion, Reply
from community.services.moderation import should_auto_approve_reply

User = get_user_model()


class ModerationServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(
            username='moderationuser',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='سلامت',
            slug='سلامت',
        )
        cls.discussion = Discussion.objects.create(
            author=cls.user,
            category=cls.category,
            title='بحث',
            slug='بحث',
            body='متن',
            last_activity_at=timezone.now(),
        )

    def test_contains_link_is_never_auto_approved(self):
        approved, reason = should_auto_approve_reply(
            self.user,
            'ببینید https://example.com',
        )
        self.assertFalse(approved)
        self.assertEqual(reason, ModerationReason.CONTAINS_LINK)

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=2)
    def test_new_user_requires_trust_threshold(self):
        approved, reason = should_auto_approve_reply(self.user, 'پاسخ ساده')
        self.assertFalse(approved)
        self.assertEqual(reason, ModerationReason.NEW_USER)

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=2)
    def test_trusted_user_is_auto_approved(self):
        for index in range(2):
            Reply.objects.create(
                discussion=self.discussion,
                author=self.user,
                body=f'پاسخ {index}',
                approved=True,
            )
        approved, reason = should_auto_approve_reply(self.user, 'پاسخ معتبر')
        self.assertTrue(approved)
        self.assertIsNone(reason)

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=5)
    def test_uses_settings_not_hardcoded_threshold(self):
        for _ in range(4):
            Reply.objects.create(
                discussion=self.discussion,
                author=self.user,
                body='پاسخ',
                approved=True,
            )
        approved, reason = should_auto_approve_reply(self.user, 'هنوز جدید')
        self.assertFalse(approved)
        self.assertEqual(reason, ModerationReason.NEW_USER)
