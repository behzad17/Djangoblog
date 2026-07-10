from django.contrib.auth import get_user_model
from django.test import TestCase

from community.models import CommunityCategory
from community.selectors.replies import (
    count_public_replies,
    list_pending_replies,
    list_public_replies,
    list_replies,
    list_replies_by_author,
)
from community.services.discussions import create_discussion
from community.services.replies import create_reply

User = get_user_model()


class ReplySelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='replyselector',
            password='password123',
        )
        cls.other = User.objects.create_user(
            username='replyother',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='پاسخ',
            slug='reply-category',
        )
        cls.discussion = create_discussion(
            author=cls.author,
            category=cls.category,
            title='بحث پاسخ',
            body='متن',
        )

    def setUp(self):
        self.approved = create_reply(
            discussion=self.discussion,
            author=self.other,
            body='پاسخ تایید شده',
        )
        self.approved.approved = True
        self.approved.moderation_reason = None
        self.approved.save(update_fields=['approved', 'moderation_reason'])

        self.pending = create_reply(
            discussion=self.discussion,
            author=self.other,
            body='پاسخ در انتظار',
        )

    def test_list_replies_returns_all_in_chronological_order(self):
        results = list(list_replies(self.discussion))
        self.assertEqual(results, [self.approved, self.pending])

    def test_list_public_replies_returns_only_approved(self):
        results = list(list_public_replies(self.discussion))
        self.assertEqual(results, [self.approved])

    def test_count_public_replies(self):
        self.assertEqual(count_public_replies(self.discussion), 1)

    def test_list_pending_replies(self):
        results = list(list_pending_replies())
        self.assertIn(self.pending, results)
        self.assertNotIn(self.approved, results)

    def test_list_replies_by_author_returns_only_approved(self):
        results = list(list_replies_by_author(self.other))
        self.assertEqual(results, [self.approved])

    def test_list_public_replies_uses_select_related(self):
        with self.assertNumQueries(1):
            replies = list(list_public_replies(self.discussion))
            for reply in replies:
                self.assertEqual(reply.discussion.title, self.discussion.title)
                self.assertEqual(reply.author.username, self.other.username)
