from datetime import date, timedelta
from io import StringIO
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.utils import timezone

from ads.models import Ad, AdCategory
from blog.models import Category, Post
from notifications.constants import NotificationType
from notifications.models import Notification
from notifications.services import NotificationService
from notifications.tasks import (
    build_weekly_digest_stats,
    get_expiring_ads,
    send_expiring_ad_notifications,
    send_weekly_digest,
)

FRIDAY = date(2024, 1, 5)
NON_FRIDAY = date(2024, 1, 6)


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@test.com',
    ADMIN_NOTIFICATION_ENABLED=False,
)
class ExpiringAdNotificationCommandTests(TestCase):
    def setUp(self):
        Site.objects.update_or_create(
            pk=settings.SITE_ID,
            defaults={'domain': 'testserver', 'name': 'Peyvand'},
        )
        self.owner = User.objects.create_user(
            username='adowner',
            email='owner@test.com',
            password='password123',
        )
        self.category = AdCategory.objects.create(name='Services', slug='services')

    def _create_ad(self, **kwargs):
        today = timezone.localdate()
        defaults = {
            'title': 'Expiring Ad',
            'slug': 'expiring-ad',
            'category': self.category,
            'owner': self.owner,
            'image': 'test/ad-image',
            'target_url': 'https://example.com',
            'is_approved': True,
            'is_active': True,
            'url_approved': True,
            'end_date': today + timedelta(days=7),
        }
        defaults.update(kwargs)
        return Ad.objects.create(**defaults)

    def test_get_expiring_ads_filters_by_exact_end_date(self):
        matching = self._create_ad(slug='match')
        self._create_ad(slug='other-date', end_date=timezone.localdate() + timedelta(days=3))

        ads = list(get_expiring_ads(days=7))

        self.assertEqual(len(ads), 1)
        self.assertEqual(ads[0].pk, matching.pk)

    def test_command_sends_notification_and_email(self):
        ad = self._create_ad()

        with self.captureOnCommitCallbacks(execute=True):
            summary = send_expiring_ad_notifications(days=7, dry_run=False)

        self.assertEqual(summary['sent'], 1)
        notification = Notification.objects.get()
        self.assertEqual(notification.notification_type, NotificationType.AD_EXPIRING)
        self.assertEqual(notification.recipient, self.owner)
        self.assertTrue(notification.email_sent)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(ad.title, mail.outbox[0].body)

    def test_command_skips_duplicate_notifications(self):
        self._create_ad()

        with self.captureOnCommitCallbacks(execute=True):
            send_expiring_ad_notifications(days=7, dry_run=False)

        summary = send_expiring_ad_notifications(days=7, dry_run=False)

        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(summary['skipped_dedup'], 1)
        self.assertEqual(summary['sent'], 0)
        self.assertEqual(len(mail.outbox), 1)

    def test_command_dry_run_creates_nothing(self):
        self._create_ad()

        summary = send_expiring_ad_notifications(days=7, dry_run=True)

        self.assertEqual(summary['sent'], 1)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_management_command_output(self):
        self._create_ad()
        stdout = StringIO()

        call_command('send_expiring_ad_notifications', '--dry-run', stdout=stdout)

        self.assertIn('DRY RUN', stdout.getvalue())
        self.assertIn('1 candidate', stdout.getvalue())


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='noreply@test.com',
)
class WeeklyDigestCommandTests(TestCase):
    def setUp(self):
        Site.objects.update_or_create(
            pk=settings.SITE_ID,
            defaults={'domain': 'testserver', 'name': 'Peyvand'},
        )
        self.subscriber = User.objects.create_user(
            username='digestuser',
            email='digest@test.com',
            password='password123',
        )
        self.opted_out = User.objects.create_user(
            username='nodigest',
            email='nodigest@test.com',
            password='password123',
        )
        NotificationService.get_or_create_preferences(self.subscriber)
        preferences = NotificationService.get_or_create_preferences(self.opted_out)
        preferences.weekly_digest = False
        preferences.save(update_fields=['weekly_digest'])

        self.category = Category.objects.create(name='News', slug='news')
        self.events_category = Category.objects.create(
            name='Events',
            slug='events-announcements',
        )
        self.author = User.objects.create_user(
            username='author',
            email='author@test.com',
            password='password123',
        )
        prefs = NotificationService.get_or_create_preferences(self.author)
        prefs.weekly_digest = False
        prefs.save(update_fields=['weekly_digest'])
        self.ad_category = AdCategory.objects.create(name='Biz', slug='biz')

    def test_build_weekly_digest_stats_counts_activity(self):
        Post.objects.create(
            title='Article',
            slug='article',
            author=self.author,
            content='Body',
            status=1,
            category=self.category,
        )
        Post.objects.create(
            title='Event',
            slug='event-post',
            author=self.author,
            content='Body',
            status=1,
            category=self.events_category,
        )
        Ad.objects.create(
            title='Business',
            slug='business-ad',
            category=self.ad_category,
            owner=self.subscriber,
            image='test/ad',
            target_url='https://example.com',
            is_approved=True,
            is_active=True,
            url_approved=True,
            plan='pro',
        )

        period_end = timezone.localdate()
        period_start = period_end - timedelta(days=7)
        stats = build_weekly_digest_stats(period_start, period_end)

        self.assertGreaterEqual(stats['new_articles'], 1)
        self.assertGreaterEqual(stats['new_events'], 1)
        self.assertNotIn('new_questions', stats)
        self.assertGreaterEqual(stats['new_businesses'], 1)
        self.assertGreaterEqual(stats['new_pro_ads'], 1)

    def test_send_weekly_digest_skips_on_non_friday(self):
        with patch('notifications.tasks.timezone.localdate', return_value=NON_FRIDAY):
            summary = send_weekly_digest(dry_run=False)

        self.assertTrue(summary['skipped_weekday'])
        self.assertEqual(summary['sent'], 0)
        self.assertEqual(summary['recipients'], 0)
        self.assertEqual(len(mail.outbox), 0)

    @patch('notifications.tasks.timezone.localdate', return_value=FRIDAY)
    def test_send_weekly_digest_emails_opted_in_users_only(self, _mock_localdate):
        summary = send_weekly_digest(dry_run=False)

        self.assertFalse(summary['skipped_weekday'])
        self.assertEqual(summary['recipients'], 1)
        self.assertEqual(summary['sent'], 1)
        self.assertEqual(Notification.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ['digest@test.com'])
        self.assertIn('آنچه این هفته در پیوند اتفاق افتاد', mail.outbox[0].subject)

    @patch('notifications.tasks.timezone.localdate', return_value=FRIDAY)
    def test_send_weekly_digest_dry_run_sends_nothing(self, _mock_localdate):
        summary = send_weekly_digest(dry_run=True)

        self.assertFalse(summary['skipped_weekday'])
        self.assertEqual(summary['recipients'], 1)
        self.assertEqual(summary['sent'], 1)
        self.assertEqual(len(mail.outbox), 0)

    def test_send_weekly_digest_dry_run_skips_on_non_friday(self):
        with patch('notifications.tasks.timezone.localdate', return_value=NON_FRIDAY):
            summary = send_weekly_digest(dry_run=True)

        self.assertTrue(summary['skipped_weekday'])
        self.assertEqual(summary['sent'], 0)
        self.assertEqual(len(mail.outbox), 0)

    @patch('notifications.tasks.timezone.localdate', return_value=FRIDAY)
    def test_send_weekly_digest_respects_user_id_filter(self, _mock_localdate):
        summary = send_weekly_digest(dry_run=False, user_id=self.subscriber.id)

        self.assertEqual(summary['recipients'], 1)
        self.assertEqual(summary['sent'], 1)

    @patch('notifications.tasks.timezone.localdate', return_value=FRIDAY)
    def test_management_command_dry_run(self, _mock_localdate):
        stdout = StringIO()
        call_command('send_weekly_digest', '--dry-run', stdout=stdout)

        self.assertIn('DRY RUN', stdout.getvalue())
        self.assertIn('articles=', stdout.getvalue())
        self.assertEqual(len(mail.outbox), 0)

    def test_management_command_skips_on_non_friday(self):
        stdout = StringIO()
        with patch('notifications.tasks.timezone.localdate', return_value=NON_FRIDAY):
            call_command('send_weekly_digest', stdout=stdout)

        self.assertIn('skipped', stdout.getvalue())
        self.assertIn('Friday', stdout.getvalue())
        self.assertEqual(len(mail.outbox), 0)
