import cloudinary
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from django.urls import reverse

User = get_user_model()


@override_settings(
    CONTENT_AI_PROVIDER='mock',
    ADMIN_NOTIFICATION_ENABLED=False,
)
class AdminAssistantUxChromeTests(TestCase):
    """UI presence checks for editorial experience polish (no AI behaviour change)."""

    def setUp(self):
        cloudinary.config(cloud_name='test', api_key='test', api_secret='test')
        self.client = Client()
        self.staff = User.objects.create_user(
            username='uxstaff',
            password='password123',
            is_staff=True,
        )
        for codename in ('add_post', 'change_post', 'view_post'):
            perm = Permission.objects.get(
                content_type__app_label='blog',
                codename=codename,
            )
            self.staff.user_permissions.add(perm)
        self.client.force_login(self.staff)

    def test_loading_and_keyboard_chrome_present(self):
        response = self.client.get(reverse('admin:blog_post_add'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="ai-assistant-loading"')
        self.assertContains(response, 'ai-assistant-spinner')
        self.assertContains(response, 'Preparing request')
        self.assertContains(response, 'aria-keyshortcuts="Control+Enter Meta+Enter"')
        self.assertContains(response, 'Ctrl/Cmd+Enter generate')
        self.assertContains(response, 'role="dialog"')
        self.assertContains(response, 'aria-modal="true"')

    def test_copy_and_telemetry_chrome_present(self):
        response = self.client.get(reverse('admin:blog_post_add'))
        self.assertContains(response, 'data-ai-copy="title"')
        self.assertContains(response, 'data-ai-copy="summary"')
        self.assertContains(response, 'data-ai-copy="body"')
        self.assertContains(response, 'data-ai-copy="all"')
        self.assertContains(response, 'id="ai-preview-telemetry-summary"')
        self.assertContains(response, 'id="ai-preview-diff-details"')
        self.assertContains(response, 'Changes from previous version')

    def test_static_assets_referenced(self):
        response = self.client.get(reverse('admin:blog_post_add'))
        self.assertContains(response, 'admin_ai_assistant.js')
        self.assertContains(response, 'admin_ai_assistant.css')
