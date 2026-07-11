from django.contrib.auth import get_user_model
from django.test import TestCase

from community.constants import DiscussionStatus
from community.models import CommunityCategory, Discussion, Reply
from community.selectors.stats import get_community_home_stats
from community.services.discussions import create_discussion

User = get_user_model()


class CommunityHomeStatsSelectorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create_user(
            username='author',
            password='password123',
        )
        cls.replier = User.objects.create_user(
            username='replier',
            password='password123',
        )
        cls.category = CommunityCategory.objects.create(
            name='مهاجرت',
            slug='immigration',
        )
        cls.inactive_category = CommunityCategory.objects.create(
            name='غیرفعال',
            slug='inactive',
            is_active=False,
        )
        cls.discussion = create_discussion(
            author=cls.author,
            category=cls.category,
            title='سؤال درباره مهاجرت',
            body='متن بحث',
        )

    def test_counts_public_discussions_replies_categories_and_members(self):
        Reply.objects.create(
            discussion=self.discussion,
            author=self.replier,
            body='پاسخ تأیید شده',
            approved=True,
        )

        stats = get_community_home_stats()

        self.assertEqual(stats['total_discussions'], 1)
        self.assertEqual(stats['total_replies'], 1)
        self.assertEqual(stats['categories'], 1)
        self.assertEqual(stats['active_members'], 2)

    def test_excludes_hidden_deleted_and_unapproved_content(self):
        Reply.objects.create(
            discussion=self.discussion,
            author=self.replier,
            body='پاسخ در انتظار',
            approved=False,
        )
        hidden = create_discussion(
            author=self.author,
            category=self.category,
            title='بحث مخفی',
            body='متن',
        )
        hidden.status = DiscussionStatus.HIDDEN
        hidden.save(update_fields=['status'])

        deleted = create_discussion(
            author=self.replier,
            category=self.category,
            title='بحث حذف شده',
            body='متن',
        )
        deleted.is_deleted = True
        deleted.save(update_fields=['is_deleted'])

        stats = get_community_home_stats()

        self.assertEqual(stats['total_discussions'], 1)
        self.assertEqual(stats['total_replies'], 0)
        self.assertEqual(stats['active_members'], 1)
