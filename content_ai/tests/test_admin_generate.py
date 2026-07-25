from unittest.mock import patch

import cloudinary
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from blog.models import Category, Post
from content_ai.admin_editorial import SESSION_SUGGESTION_KEY
from content_ai.editorial.drafts import EditorialDraft
from content_ai.providers.exceptions import GenerationError
from content_ai.telemetry import AIExecutionTelemetry

User = get_user_model()


@override_settings(
    CONTENT_AI_PROVIDER='mock',
    ADMIN_NOTIFICATION_ENABLED=False,
)
class AdminGenerateWithAITests(TestCase):
    def setUp(self):
        cloudinary.config(
            cloud_name='test',
            api_key='test',
            api_secret='test',
        )
        self.client = Client()
        self.category = Category.objects.create(
            name='Admin AI Category',
            slug='admin-ai-category',
        )
        self.staff = User.objects.create_user(
            username='aistaff',
            password='password123',
            is_staff=True,
        )
        for codename in ('add_post', 'change_post', 'view_post'):
            perm = Permission.objects.get(
                content_type__app_label='blog',
                codename=codename,
            )
            self.staff.user_permissions.add(perm)

        self.author = User.objects.create_user(
            username='aiauthor',
            password='password123',
        )
        self.draft = Post.objects.create(
            title='Existing Draft Post',
            slug='existing-draft-post',
            author=self.author,
            category=self.category,
            content='Draft body',
            status=0,
        )
        self.published = Post.objects.create(
            title='Existing Published Post',
            slug='existing-published-post',
            author=self.author,
            category=self.category,
            content='Published body',
            status=1,
        )
        self.generate_url = reverse('admin:blog_post_generate_with_ai')
        self.add_url = reverse('admin:blog_post_add')

    def _login_staff(self):
        self.client.force_login(self.staff)

    def test_anonymous_redirected(self):
        response = self.client.get(self.generate_url)
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_non_staff_forbidden(self):
        user = User.objects.create_user(username='plain', password='password123')
        self.client.force_login(user)
        response = self.client.get(self.generate_url)
        self.assertEqual(response.status_code, 302)

    def test_staff_without_blog_permission_denied(self):
        bare_staff = User.objects.create_user(
            username='barestaff',
            password='password123',
            is_staff=True,
        )
        self.client.force_login(bare_staff)
        response = self.client.get(self.generate_url)
        self.assertEqual(response.status_code, 403)

    def test_button_visible_on_add(self):
        self._login_staff()
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generate with AI')
        self.assertContains(response, self.generate_url)

    def test_button_visible_on_draft(self):
        self._login_staff()
        url = reverse('admin:blog_post_change', args=[self.draft.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generate with AI')
        self.assertContains(response, f'post_id={self.draft.pk}')

    def test_button_hidden_on_published(self):
        self._login_staff()
        url = reverse('admin:blog_post_change', args=[self.published.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Generate with AI')

    def test_published_generate_url_blocked(self):
        self._login_staff()
        response = self.client.get(
            self.generate_url,
            {'post_id': self.published.pk},
            follow=True,
        )
        self.assertContains(
            response,
            'Generate with AI is only available for Draft posts.',
        )

    @patch('blog.admin.EditorialAIService.generate_draft')
    def test_successful_generation_populates_add_form(self, mock_generate):
        mock_generate.return_value = EditorialDraft(
            title='AI Suggested Title',
            body='AI suggested body content',
            summary='AI summary',
            language='sv',
            metadata={'provider': 'mock'},
            telemetry=AIExecutionTelemetry(
                provider='mock',
                model='mock',
                success=True,
                duration_ms=1.0,
            ),
        )
        self._login_staff()
        before = Post.objects.count()
        response = self.client.post(
            self.generate_url,
            {
                'title': 'Working title',
                'category': self.category.pk,
                'language': 'sv',
                'context': 'Housing news',
                'instructions': 'Keep short',
                'generate': 'Generate',
            },
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, self.add_url)
        self.assertEqual(Post.objects.count(), before)

        follow = self.client.get(self.add_url)
        self.assertEqual(follow.status_code, 200)
        self.assertContains(follow, 'AI suggestion loaded')
        self.assertContains(follow, 'AI Suggested Title')
        self.assertContains(follow, 'AI suggested body content')
        self.assertContains(follow, 'AI summary')
        # Still only a suggestion — no auto-save.
        self.assertEqual(Post.objects.count(), before)
        self.assertNotIn(SESSION_SUGGESTION_KEY, self.client.session)

    @patch('blog.admin.EditorialAIService.generate_draft')
    def test_successful_generation_on_draft(self, mock_generate):
        mock_generate.return_value = EditorialDraft(
            title='Updated AI Title',
            body='Updated AI body',
            summary='Updated summary',
            language='fa',
            metadata={'provider': 'mock'},
        )
        self._login_staff()
        before = Post.objects.count()
        response = self.client.post(
            f'{self.generate_url}?post_id={self.draft.pk}',
            {
                'post_id': self.draft.pk,
                'title': 'Existing Draft Post',
                'category': self.category.pk,
                'language': 'fa',
                'context': 'ctx',
                'instructions': 'instr',
                'generate': 'Generate',
            },
        )
        self.assertEqual(response.status_code, 302)
        change_url = reverse('admin:blog_post_change', args=[self.draft.pk])
        self.assertEqual(response.url, change_url)
        self.assertEqual(Post.objects.count(), before)

        follow = self.client.get(change_url)
        self.assertContains(follow, 'Updated AI Title')
        self.assertContains(follow, 'Updated AI body')
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.content, 'Draft body')
        self.assertEqual(self.draft.status, 0)

    @patch('blog.admin.EditorialAIService.generate_draft')
    def test_provider_failure_shows_error(self, mock_generate):
        mock_generate.side_effect = GenerationError('provider exploded')
        self._login_staff()
        before = Post.objects.count()
        response = self.client.post(
            self.generate_url,
            {
                'title': 'Failing title',
                'category': self.category.pk,
                'language': 'sv',
                'context': '',
                'instructions': '',
                'generate': 'Generate',
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'provider exploded')
        self.assertEqual(Post.objects.count(), before)
        self.assertNotIn(SESSION_SUGGESTION_KEY, self.client.session)

    @patch('blog.admin.EditorialAIService.generate_draft')
    def test_draft_status_forced_in_suggestion(self, mock_generate):
        mock_generate.return_value = EditorialDraft(
            title='Status Check',
            body='Body',
            summary='Summary',
            language='sv',
            metadata={},
        )
        self._login_staff()
        self.client.post(
            self.generate_url,
            {
                'title': 'Status Check',
                'category': self.category.pk,
                'language': 'sv',
                'generate': 'Generate',
            },
        )
        suggestion = self.client.session.get(SESSION_SUGGESTION_KEY)
        self.assertIsNotNone(suggestion)
        self.assertEqual(suggestion['status'], 0)
        self.assertEqual(suggestion['category_id'], self.category.pk)
        self.assertEqual(suggestion['content'], 'Body')
        self.assertEqual(suggestion['excerpt'], 'Summary')
