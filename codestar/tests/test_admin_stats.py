from django.contrib.auth import get_user_model
from django.test import TestCase

from codestar.admin_stats import get_admin_stats
from community.constants import DiscussionStatus
from community.models import CommunityCategory
from community.services.discussions import create_discussion
from community.services.replies import create_reply

User = get_user_model()


class AdminStatsCommunityTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='adminstatsuser',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='آمار',
            slug='admin-stats-category',
        )

    def test_get_admin_stats_includes_pending_community_counts(self):
        hidden = create_discussion(
            author=self.author,
            category=self.category,
            title='بحث مخفی',
            body='متن',
        )
        hidden.status = DiscussionStatus.HIDDEN
        hidden.save(update_fields=['status'])

        discussion = create_discussion(
            author=self.author,
            category=self.category,
            title='بحث باز',
            body='متن',
        )
        create_reply(
            discussion=discussion,
            author=self.author,
            body='پاسخ در انتظار',
        )

        stats = get_admin_stats()

        self.assertEqual(stats['pending_community_discussions'], 1)
        self.assertEqual(stats['pending_community_replies'], 1)
