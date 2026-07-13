from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.models import Site
from django.core import mail
from django.test import TestCase, override_settings

from notifications.constants import NotificationType
from notifications.models import Notification, NotificationPreference
from notifications.services import NotificationService

User = get_user_model()


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@test.com',
)
class NotificationServiceTests(TestCase):
    def setUp(self):
        Site.objects.update_or_create(
            pk=settings.SITE_ID,
            defaults={'domain': 'testserver', 'name': 'Peyvand'},
        )
        self.user = User.objects.create_user(
            username='notifyuser',
            email='notifyuser@test.com',
            password='password123',
        )

    def test_preference_defaults(self):
        preferences = NotificationService.get_or_create_preferences(self.user)

        self.assertTrue(preferences.askme_emails)
        self.assertTrue(preferences.ad_emails)
        self.assertTrue(preferences.favorite_notifications)
        self.assertTrue(preferences.weekly_digest)
        self.assertTrue(preferences.comment_notifications)

    def test_creates_in_app_notification(self):
        notification = NotificationService.notify(
            recipient=self.user,
            notification_type=NotificationType.AD_APPROVED,
            title='آگهی شما منتشر شد',
            message='آگهی شما تایید شد.',
            url='/ads/example/',
        )

        self.assertIsNotNone(notification)
        self.assertEqual(Notification.objects.count(), 1)
        self.assertFalse(notification.email_sent)
        self.assertIsNone(notification.email_sent_at)

    def test_marks_email_sent_at_after_successful_send(self):
        with self.captureOnCommitCallbacks(execute=True):
            notification = NotificationService.notify(
                recipient=self.user,
                notification_type=NotificationType.AD_APPROVED,
                title='آگهی شما منتشر شد',
                message='آگهی شما تایید شد.',
                url='/ads/example/',
                send_email=True,
                email_context={
                    'ad_title': 'آگهی تست',
                    'cta_url': 'https://peyvand.se/ads/example/',
                    'cta_text': 'مشاهده آگهی',
                },
            )

        notification.refresh_from_db()
        self.assertTrue(notification.email_sent)
        self.assertIsNotNone(notification.email_sent_at)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('آگهی شما در پیوند تایید شد', mail.outbox[0].subject)

    def test_respects_dedup_key(self):
        NotificationService.notify(
            recipient=self.user,
            notification_type=NotificationType.AD_EXPIRING,
            title='آگهی شما به زودی منقضی می‌شود',
            message='۷ روز تا پایان اعتبار آگهی شما باقی مانده است.',
            dedup_key='ad:1:7day',
        )
        duplicate = NotificationService.notify(
            recipient=self.user,
            notification_type=NotificationType.AD_EXPIRING,
            title='آگهی شما به زودی منقضی می‌شود',
            message='۷ روز تا پایان اعتبار آگهی شما باقی مانده است.',
            dedup_key='ad:1:7day',
        )

        self.assertEqual(Notification.objects.count(), 1)
        self.assertIsNone(duplicate)

    def test_weekly_digest_email_only(self):
        sent = NotificationService.send_email_only(
            recipient=self.user,
            notification_type=NotificationType.WEEKLY_DIGEST,
            email_context={
                'summary_lines': [
                    {'emoji': '📰', 'text': '3 مقاله جدید'},
                    {'emoji': '📅', 'text': '1 رویداد جدید'},
                ],
                'featured_items': [
                    {
                        'title': 'Featured Article',
                        'description': 'Short description',
                        'url': 'https://peyvand.se/article/',
                        'thumbnail_url': None,
                    }
                ],
                'cta_url': 'https://peyvand.se/this-week/',
                'cta_text': 'مشاهده همه 3 مقاله',
            },
        )

        self.assertTrue(sent)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('آنچه این هفته در پیوند اتفاق افتاد', mail.outbox[0].subject)
        self.assertIn('منتخب این هفته', mail.outbox[0].body)
        self.assertNotIn('سوال جدید', mail.outbox[0].body)

    def test_favorite_copy_constant(self):
        from notifications.constants import IN_APP_MESSAGES

        self.assertEqual(
            IN_APP_MESSAGES[NotificationType.AD_FAVORITED]['message'],
            'آگهی شما به فهرست علاقه‌مندی‌های یک کاربر اضافه شد.',
        )

    def test_specialist_answer_email_uses_generic_copy(self):
        with self.captureOnCommitCallbacks(execute=True):
            NotificationService.notify(
                recipient=self.user,
                notification_type=NotificationType.ASKME_SPECIALIST_ANSWER,
                title='پاسخ متخصص دریافت کردید',
                message='یک متخصص به سوال شما پاسخ داد.',
                send_email=True,
                email_context={
                    'cta_url': 'https://peyvand.se/ask-me/my-questions/',
                    'cta_text': 'مشاهده پاسخ متخصص',
                },
            )

        body = mail.outbox[0].body
        self.assertIn('به سوال شما در پیوند پاسخ داده شد', body)
        self.assertNotIn('question_text', body)
