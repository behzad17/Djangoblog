from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

from notifications.constants import NotificationType
from notifications.models import Notification
from notifications.services import NotificationService


class NotificationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='notifyviewer',
            email='viewer@test.com',
            password='password123',
        )
        self.other = User.objects.create_user(
            username='otheruser',
            email='other@test.com',
            password='password123',
        )
        self.client = Client()

    def _create_notification(self, **kwargs):
        defaults = {
            'recipient': self.user,
            'notification_type': NotificationType.AD_APPROVED,
            'title': 'آگهی شما منتشر شد',
            'message': 'آگهی شما تایید شد.',
            'url': '/ads/test-ad/',
            'is_read': False,
        }
        defaults.update(kwargs)
        return Notification.objects.create(**defaults)

    def test_dropdown_requires_authentication(self):
        response = self.client.get(reverse('notifications:dropdown'))
        self.assertEqual(response.status_code, 302)

    def test_dropdown_returns_at_most_ten_notifications(self):
        for index in range(12):
            self._create_notification(
                title=f'Notification {index}',
                message=f'Message {index}',
            )

        self.client.login(username='notifyviewer', password='password123')
        response = self.client.get(
            reverse('notifications:dropdown'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.decode().count('data-notification-id='), 10)
        self.assertContains(response, 'اعلان‌ها')
        self.assertContains(response, 'خوانده نشده')

    def test_list_page_requires_authentication(self):
        response = self.client.get(reverse('notifications:list'))
        self.assertEqual(response.status_code, 302)

    def test_list_page_renders_notifications(self):
        self._create_notification()
        self.client.login(username='notifyviewer', password='password123')

        response = self.client.get(reverse('notifications:list'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'اعلان‌ها')
        self.assertContains(response, 'آگهی شما منتشر شد')

    def test_mark_read_updates_notification(self):
        notification = self._create_notification()
        self.client.login(username='notifyviewer', password='password123')

        response = self.client.post(reverse('notifications:mark_read', args=[notification.id]))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['unread_count'], 0)
        notification.refresh_from_db()
        self.assertTrue(notification.is_read)

    def test_mark_read_denies_other_users(self):
        notification = self._create_notification()
        self.client.login(username='otheruser', password='password123')

        response = self.client.post(reverse('notifications:mark_read', args=[notification.id]))

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()['success'])
        notification.refresh_from_db()
        self.assertFalse(notification.is_read)

    def test_mark_all_read(self):
        self._create_notification()
        self._create_notification(title='Second')
        self.client.login(username='notifyviewer', password='password123')

        response = self.client.post(reverse('notifications:mark_all_read'))

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['unread_count'], 0)
        self.assertEqual(
            Notification.objects.filter(recipient=self.user, is_read=False).count(),
            0,
        )

    def test_context_processor_exposes_unread_count(self):
        self._create_notification()
        self._create_notification(is_read=True, title='Read one')
        self.client.login(username='notifyviewer', password='password123')

        response = self.client.get(reverse('home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'notificationBellRoot')
        self.assertContains(response, 'notificationBellBadge')

    def test_mobile_drawer_shows_notifications_link(self):
        self._create_notification()
        self.client.login(username='notifyviewer', password='password123')

        response = self.client.get(reverse('home'))

        self.assertContains(response, reverse('notifications:list'))
        self.assertContains(response, 'mobile-nav-drawer-cta__btn--notifications')
        self.assertContains(response, 'اعلان‌ها')

    def test_dropdown_shows_unread_count_in_header(self):
        self._create_notification()
        self._create_notification(title='Second unread')
        NotificationService.mark_all_read(self.user)
        unread = self._create_notification(title='Fresh unread')

        self.client.login(username='notifyviewer', password='password123')
        response = self.client.get(
            reverse('notifications:dropdown'),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertContains(response, '1')
        self.assertContains(response, 'خوانده نشده')
        self.assertContains(response, unread.title)

    def test_list_page_loads_notifications_js_once(self):
        self.client.login(username='notifyviewer', password='password123')
        response = self.client.get(reverse('notifications:list'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content.count(b'js/notifications.js'), 1)
