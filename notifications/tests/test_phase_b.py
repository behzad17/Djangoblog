from django.conf import settings
from django.contrib.admin.sites import AdminSite
from django.contrib.auth.models import User
from django.contrib.messages.storage.fallback import FallbackStorage
from django.contrib.sites.models import Site
from django.core import mail
from django.test import RequestFactory, TestCase, override_settings

from ads.admin import AdAdmin
from ads.models import Ad, AdCategory, FavoriteAd
from askme.models import Moderator, Question
from blog.models import UserProfile
from notifications.constants import IN_APP_MESSAGES, NotificationType
from notifications.models import Notification, NotificationPreference
from notifications.services import NotificationService


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@test.com',
    ADMIN_NOTIFICATION_ENABLED=False,
)
class PhaseBNotificationTests(TestCase):
    def setUp(self):
        Site.objects.update_or_create(
            pk=settings.SITE_ID,
            defaults={'domain': 'testserver', 'name': 'Peyvand'},
        )

        self.asker = User.objects.create_user(
            username='asker',
            email='asker@test.com',
            password='password123',
        )
        self.owner = User.objects.create_user(
            username='adowner',
            email='owner@test.com',
            password='password123',
        )
        self.favoriter = User.objects.create_user(
            username='favoriter',
            email='favoriter@test.com',
            password='password123',
        )
        self.moderator_user = User.objects.create_user(
            username='moderator',
            email='moderator@test.com',
            password='password123',
        )

        for user in (self.asker, self.owner, self.favoriter, self.moderator_user):
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'is_site_verified': True},
            )

        self.moderator = Moderator.objects.create(
            user=self.moderator_user,
            expert_title='Lawyer',
            complete_name='Test Moderator',
            slug='test-moderator',
        )
        self.category = AdCategory.objects.create(
            name='Services',
            slug='services',
        )

    def _create_question(self, answered=False):
        return Question.objects.create(
            user=self.asker,
            moderator=self.moderator,
            question_text='Private question content should never leak.',
            answer_text='Private answer' if answered else '',
            answered=answered,
        )

    def _create_ad(self, **kwargs):
        defaults = {
            'title': 'Test Ad',
            'slug': 'test-ad',
            'category': self.category,
            'owner': self.owner,
            'image': 'test/ad-image',
            'target_url': 'https://example.com',
            'is_active': True,
            'is_approved': False,
            'url_approved': True,
            'plan': 'free',
        }
        defaults.update(kwargs)
        return Ad.objects.create(**defaults)

    def test_askme_specialist_answer_creates_notification_and_email(self):
        question = self._create_question()

        with self.captureOnCommitCallbacks(execute=True):
            question.answered = True
            question.save(update_fields=['answered'])

        notification = Notification.objects.get()
        self.assertEqual(notification.recipient, self.asker)
        self.assertEqual(
            notification.notification_type,
            NotificationType.ASKME_SPECIALIST_ANSWER,
        )
        self.assertEqual(notification.actor, self.moderator_user)
        self.assertTrue(notification.email_sent)
        self.assertIsNotNone(notification.email_sent_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('به سوال شما در پیوند پاسخ داده شد', mail.outbox[0].body)
        self.assertNotIn('Private question content', mail.outbox[0].body)

    def test_askme_email_respects_preferences(self):
        preferences = NotificationService.get_or_create_preferences(self.asker)
        preferences.askme_emails = False
        preferences.save(update_fields=['askme_emails'])

        question = self._create_question()
        with self.captureOnCommitCallbacks(execute=True):
            question.answered = True
            question.save(update_fields=['answered'])

        notification = Notification.objects.get()
        self.assertFalse(notification.email_sent)
        self.assertEqual(len(mail.outbox), 0)

    def test_askme_does_not_notify_when_already_answered(self):
        question = self._create_question(answered=True)

        question.answer_text = 'Updated answer'
        question.save(update_fields=['answer_text'])

        self.assertEqual(Notification.objects.count(), 0)

    def test_ad_approved_notification(self):
        ad = self._create_ad(is_approved=False)

        with self.captureOnCommitCallbacks(execute=True):
            ad.is_approved = True
            ad.save(update_fields=['is_approved'])

        notification = Notification.objects.get()
        self.assertEqual(notification.notification_type, NotificationType.AD_APPROVED)
        self.assertEqual(notification.recipient, self.owner)
        self.assertTrue(notification.email_sent)
        self.assertIn('آگهی شما در پیوند تایید شد', mail.outbox[0].subject)

    def test_ad_approved_not_sent_on_initial_create(self):
        self._create_ad(is_approved=False)
        self.assertEqual(Notification.objects.count(), 0)

    def test_ad_rejected_only_via_admin_action(self):
        ad = self._create_ad(is_approved=False)
        ad.is_active = True
        ad.save(update_fields=['is_active'])

        self.assertEqual(Notification.objects.count(), 0)

        request = RequestFactory().post('/admin/ads/ad/')
        request.user = self.owner
        request.session = {}
        request._messages = FallbackStorage(request)

        admin = AdAdmin(Ad, AdminSite())
        with self.captureOnCommitCallbacks(execute=True):
            admin.reject_selected_ads(request, Ad.objects.filter(pk=ad.pk))

        notification = Notification.objects.get()
        self.assertEqual(notification.notification_type, NotificationType.AD_REJECTED)
        self.assertEqual(notification.recipient, self.owner)
        self.assertTrue(notification.email_sent)
        ad.refresh_from_db()
        self.assertFalse(ad.is_approved)
        self.assertFalse(ad.is_active)

    def test_ad_upgraded_to_pro_notification(self):
        ad = self._create_ad(is_approved=True, plan='free')

        with self.captureOnCommitCallbacks(execute=True):
            ad.plan = 'pro'
            ad.save(update_fields=['plan'])

        notification = Notification.objects.get()
        self.assertEqual(notification.notification_type, NotificationType.AD_PRO)
        self.assertEqual(notification.recipient, self.owner)
        self.assertTrue(notification.email_sent)

    def test_ad_favorited_in_app_only(self):
        ad = self._create_ad(is_approved=True)

        from notifications.dispatchers import notify_ad_favorited

        notify_ad_favorited(ad, self.favoriter)

        notification = Notification.objects.get()
        self.assertEqual(notification.notification_type, NotificationType.AD_FAVORITED)
        self.assertEqual(
            notification.message,
            IN_APP_MESSAGES[NotificationType.AD_FAVORITED]['message'],
        )
        self.assertEqual(notification.actor, self.favoriter)
        self.assertFalse(notification.email_sent)
        self.assertEqual(len(mail.outbox), 0)

    def test_ad_favorited_skips_owner_self_favorite(self):
        ad = self._create_ad(is_approved=True)

        from notifications.dispatchers import notify_ad_favorited

        notify_ad_favorited(ad, self.owner)
        self.assertEqual(Notification.objects.count(), 0)

    def test_ad_favorited_respects_preferences(self):
        ad = self._create_ad(is_approved=True)
        preferences = NotificationService.get_or_create_preferences(self.owner)
        preferences.favorite_notifications = False
        preferences.save(update_fields=['favorite_notifications'])

        from notifications.dispatchers import notify_ad_favorited

        notify_ad_favorited(ad, self.favoriter)
        self.assertEqual(Notification.objects.count(), 0)

    def test_add_ad_to_favorites_view_notifies_owner(self):
        ad = self._create_ad(is_approved=True, slug='favorite-ad')
        self.client.login(username='favoriter', password='password123')

        response = self.client.get(
            f'/ads/add-to-favorites/{ad.id}/',
            HTTP_REFERER='/ads/',
        )

        self.assertEqual(response.status_code, 302)
        self.assertTrue(FavoriteAd.objects.filter(user=self.favoriter, ad=ad).exists())
        notification = Notification.objects.get()
        self.assertEqual(notification.notification_type, NotificationType.AD_FAVORITED)

    def test_user_creation_auto_creates_notification_preferences(self):
        user = User.objects.create_user(
            username='newuser',
            email='newuser@test.com',
            password='password123',
        )
        preferences = NotificationPreference.objects.get(user=user)
        self.assertTrue(preferences.weekly_digest)
