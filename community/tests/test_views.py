from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from blog.models import UserProfile
from community.constants import DiscussionStatus
from community.forms import ReplyCreateForm
from community.models import CommunityCategory, Discussion, Reply
from community.services.discussions import create_discussion
from notifications.constants import NotificationType
from notifications.models import Notification

User = get_user_model()


class CommunityViewTests(TestCase):
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
        cls.other_user = User.objects.create_user(
            username='other',
            password='password123',
        )
        for user in (cls.author, cls.replier, cls.other_user):
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'is_site_verified': True},
            )

        cls.category = CommunityCategory.objects.create(
            name='مهاجرت',
            slug='immigration',
        )
        cls.discussion = create_discussion(
            author=cls.author,
            category=cls.category,
            title='سؤال درباره اقامت',
            body='متن بحث تست',
        )

    def test_community_home_redirects_to_discussion_list(self):
        response = self.client.get(reverse('community:home'))
        self.assertRedirects(response, reverse('community:discussion_list'))

    def test_discussion_list_renders(self):
        response = self.client.get(reverse('community:discussion_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'انجمن')
        self.assertContains(response, self.discussion.title)

    def test_discussion_detail_renders(self):
        response = self.client.get(
            reverse('community:discussion_detail', args=[self.discussion.slug]),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.discussion.title)
        self.assertContains(response, 'متن بحث تست')
        self.assertIsInstance(response.context['reply_form'], ReplyCreateForm)

    def test_discussion_create_requires_login(self):
        response = self.client.get(reverse('community:discussion_create'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_discussion_create_post(self):
        self.client.login(username='author', password='password123')
        response = self.client.post(
            reverse('community:discussion_create'),
            {
                'category': self.category.pk,
                'title': 'بحث جدید',
                'body': 'متن بحث جدید',
            },
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        discussion = Discussion.objects.get(title='بحث جدید')
        self.assertEqual(discussion.author, self.author)
        self.assertContains(response, 'بحث شما با موفقیت ایجاد شد.')

    def test_discussion_reply_post(self):
        self.client.login(username='replier', password='password123')
        response = self.client.post(
            reverse('community:discussion_reply', args=[self.discussion.slug]),
            {'body': 'این یک پاسخ تست است.'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        reply = Reply.objects.get(discussion=self.discussion, author=self.replier)
        self.assertEqual(reply.body, 'این یک پاسخ تست است.')

    def test_discussion_close_by_author(self):
        self.client.login(username='author', password='password123')
        response = self.client.post(
            reverse('community:discussion_close', args=[self.discussion.slug]),
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.discussion.refresh_from_db()
        self.assertEqual(self.discussion.status, DiscussionStatus.CLOSED)
        self.assertContains(response, 'بحث بسته شد')

    def test_closed_discussion_rejects_reply(self):
        self.discussion.status = DiscussionStatus.CLOSED
        self.discussion.save(update_fields=['status'])
        self.client.login(username='replier', password='password123')
        response = self.client.post(
            reverse('community:discussion_reply', args=[self.discussion.slug]),
            {'body': 'پاسخ بعد از بسته شدن'},
            follow=True,
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(
            Reply.objects.filter(
                discussion=self.discussion,
                body='پاسخ بعد از بسته شدن',
            ).exists(),
        )
        self.assertContains(response, 'امکان ثبت پاسخ')

    def test_community_search_renders(self):
        response = self.client.get(
            reverse('community:search'),
            {'q': 'اقامت'},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.discussion.title)

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=0)
    def test_approved_reply_notifies_discussion_author(self):
        self.client.login(username='replier', password='password123')
        self.client.post(
            reverse('community:discussion_reply', args=[self.discussion.slug]),
            {'body': 'پاسخ با اعلان'},
        )
        self.assertTrue(
            Notification.objects.filter(
                recipient=self.author,
                notification_type=NotificationType.COMMUNITY_REPLY,
            ).exists(),
        )

    @override_settings(COMMUNITY_TRUST_REPLY_COUNT=0)
    def test_self_reply_does_not_notify(self):
        self.client.login(username='author', password='password123')
        self.client.post(
            reverse('community:discussion_reply', args=[self.discussion.slug]),
            {'body': 'پاسخ خودم'},
        )
        self.assertFalse(
            Notification.objects.filter(
                recipient=self.author,
                notification_type=NotificationType.COMMUNITY_REPLY,
            ).exists(),
        )
