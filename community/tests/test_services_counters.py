from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from community.models import CommunityCategory, Discussion, Reply
from community.services.counters import recalculate_discussion_stats
from community.services.discussions import create_discussion

User = get_user_model()


class CounterServiceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='counterauthor',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='کار',
            slug='کار',
        )

    def test_recalculate_with_no_replies_uses_created_on(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='بدون پاسخ',
            body='متن',
        )
        updated = recalculate_discussion_stats(discussion)
        self.assertEqual(updated.reply_count, 0)
        self.assertEqual(updated.last_activity_at, updated.created_on)

    def test_recalculate_counts_only_approved_replies(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='با پاسخ',
            body='متن',
        )
        Reply.objects.create(
            discussion=discussion,
            author=self.author,
            body='در انتظار',
            approved=False,
        )
        approved = Reply.objects.create(
            discussion=discussion,
            author=self.author,
            body='تایید شده',
            approved=True,
        )
        updated = recalculate_discussion_stats(discussion)
        self.assertEqual(updated.reply_count, 1)
        self.assertEqual(updated.last_activity_at, approved.created_on)

    def test_recalculate_uses_latest_approved_reply(self):
        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='چند پاسخ',
            body='متن',
        )
        older = Reply.objects.create(
            discussion=discussion,
            author=self.author,
            body='قدیمی',
            approved=True,
        )
        Reply.objects.filter(pk=older.pk).update(
            created_on=timezone.now() - timezone.timedelta(days=2),
        )
        latest = Reply.objects.create(
            discussion=discussion,
            author=self.author,
            body='جدید',
            approved=True,
        )
        updated = recalculate_discussion_stats(discussion)
        self.assertEqual(updated.reply_count, 2)
        self.assertEqual(updated.last_activity_at, latest.created_on)
