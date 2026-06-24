from io import StringIO

from django.contrib.auth.models import User
from django.core.management import call_command
from django.test import TestCase

from notifications.models import NotificationPreference
from notifications.services import NotificationService
from notifications.tasks import backfill_notification_preferences


class BackfillNotificationPreferencesTests(TestCase):
    def setUp(self):
        self.user_without = User.objects.create_user(
            username='legacyuser',
            email='legacy@test.com',
            password='password123',
        )
        self.user_with = User.objects.create_user(
            username='existingprefs',
            email='existing@test.com',
            password='password123',
        )
        NotificationPreference.objects.filter(user=self.user_without).delete()
        self.existing_preferences = NotificationService.get_or_create_preferences(
            self.user_with
        )

    def test_creates_preferences_for_users_without_one(self):
        summary = backfill_notification_preferences()

        self.assertEqual(summary['created'], 1)
        self.assertEqual(summary['skipped'], 1)
        self.assertTrue(
            NotificationPreference.objects.filter(user=self.user_without).exists()
        )

    def test_skips_users_who_already_have_preferences(self):
        backfill_notification_preferences()

        self.assertEqual(
            NotificationPreference.objects.filter(user=self.user_with).count(),
            1,
        )
        self.existing_preferences.refresh_from_db()
        self.assertTrue(self.existing_preferences.weekly_digest)

    def test_safe_to_run_multiple_times(self):
        backfill_notification_preferences()
        summary = backfill_notification_preferences()

        self.assertEqual(summary['created'], 0)
        self.assertEqual(summary['skipped'], 2)
        self.assertEqual(NotificationPreference.objects.count(), 2)

    def test_dry_run_creates_nothing(self):
        summary = backfill_notification_preferences(dry_run=True)

        self.assertEqual(summary['created'], 1)
        self.assertEqual(summary['skipped'], 1)
        self.assertFalse(
            NotificationPreference.objects.filter(user=self.user_without).exists()
        )

    def test_management_command_output(self):
        stdout = StringIO()
        call_command('backfill_notification_preferences', stdout=stdout)

        output = stdout.getvalue()
        self.assertIn('LIVE', output)
        self.assertIn('1 created', output)
        self.assertIn('1 skipped', output)
