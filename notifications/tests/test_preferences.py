from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.test import Client, TestCase
from django.urls import reverse

from notifications.forms import NotificationPreferenceForm
from notifications.models import NotificationPreference
from notifications.services import NotificationService


class NotificationPreferenceFormTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='prefsuser',
            email='prefs@test.com',
            password='password123',
        )
        self.preferences = NotificationService.get_or_create_preferences(self.user)

    def test_form_fields_exclude_comment_notifications(self):
        form = NotificationPreferenceForm(instance=self.preferences)
        field_names = list(form.fields.keys())

        self.assertEqual(
            field_names,
            ['askme_emails', 'ad_emails', 'favorite_notifications', 'weekly_digest'],
        )
        self.assertNotIn('comment_notifications', field_names)

    def test_form_persian_labels(self):
        form = NotificationPreferenceForm(instance=self.preferences)

        self.assertEqual(
            form.fields['weekly_digest'].label,
            'خبرنامه هفتگی',
        )

    def test_form_saves_boolean_preferences(self):
        form = NotificationPreferenceForm(
            data={
                'askme_emails': True,
                'ad_emails': False,
                'favorite_notifications': True,
                'weekly_digest': False,
            },
            instance=self.preferences,
        )

        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.preferences.refresh_from_db()

        self.assertTrue(self.preferences.askme_emails)
        self.assertFalse(self.preferences.ad_emails)
        self.assertTrue(self.preferences.favorite_notifications)
        self.assertFalse(self.preferences.weekly_digest)


class NotificationPreferencesViewTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse('account_settings')
        self.user = User.objects.create_user(
            username='settingsuser',
            email='settings@test.com',
            password='password123',
        )
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            password='password123',
        )
        self.preferences = NotificationService.get_or_create_preferences(self.user)

    def test_requires_login(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 302)
        self.assertIn('/accounts/login/', response.url)

    def test_settings_page_renders_preferences_form(self):
        self.client.login(username='settingsuser', password='password123')
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'اعلان‌ها و ایمیل‌ها')
        self.assertContains(response, 'name="askme_emails"')
        self.assertContains(response, 'name="weekly_digest"')
        self.assertContains(response, 'ذخیره تنظیمات اعلان‌ها')

    def test_form_reflects_current_preferences(self):
        self.preferences.weekly_digest = False
        self.preferences.save(update_fields=['weekly_digest'])

        self.client.login(username='settingsuser', password='password123')
        response = self.client.get(self.url)
        form = response.context['notification_form']

        self.assertFalse(form.instance.weekly_digest)

    def test_post_updates_preferences(self):
        self.client.login(username='settingsuser', password='password123')
        response = self.client.post(self.url, {
            'form_type': 'notification_preferences',
            'askme_emails': 'on',
            'favorite_notifications': 'on',
        })

        self.assertRedirects(response, self.url)
        self.preferences.refresh_from_db()
        self.assertTrue(self.preferences.askme_emails)
        self.assertFalse(self.preferences.ad_emails)
        self.assertTrue(self.preferences.favorite_notifications)
        self.assertFalse(self.preferences.weekly_digest)

        messages = list(get_messages(response.wsgi_request))
        self.assertEqual(len(messages), 1)
        self.assertIn('ذخیره شد', str(messages[0]))

    def test_post_only_updates_authenticated_user_preferences(self):
        self.preferences.weekly_digest = False
        self.preferences.save(update_fields=['weekly_digest'])
        other_preferences = NotificationService.get_or_create_preferences(self.other_user)
        self.client.login(username='settingsuser', password='password123')

        self.client.post(self.url, {
            'form_type': 'notification_preferences',
            'weekly_digest': 'on',
        })

        other_preferences.refresh_from_db()
        self.preferences.refresh_from_db()
        self.assertTrue(self.preferences.weekly_digest)
        self.assertTrue(other_preferences.weekly_digest)

    def test_unchecked_checkboxes_post_as_false(self):
        self.preferences.askme_emails = True
        self.preferences.ad_emails = True
        self.preferences.favorite_notifications = True
        self.preferences.weekly_digest = True
        self.preferences.save()

        self.client.login(username='settingsuser', password='password123')
        self.client.post(self.url, {'form_type': 'notification_preferences'})

        self.preferences.refresh_from_db()
        self.assertFalse(self.preferences.askme_emails)
        self.assertFalse(self.preferences.ad_emails)
        self.assertFalse(self.preferences.favorite_notifications)
        self.assertFalse(self.preferences.weekly_digest)

    def test_post_without_form_type_does_not_update_preferences(self):
        self.preferences.weekly_digest = True
        self.preferences.save(update_fields=['weekly_digest'])

        self.client.login(username='settingsuser', password='password123')
        self.client.post(self.url, {'weekly_digest': ''})

        self.preferences.refresh_from_db()
        self.assertTrue(self.preferences.weekly_digest)

    def test_preferences_row_created_on_first_visit(self):
        NotificationPreference.objects.filter(user=self.user).delete()

        self.client.login(username='settingsuser', password='password123')
        self.client.get(self.url)

        self.assertTrue(
            NotificationPreference.objects.filter(user=self.user).exists()
        )
