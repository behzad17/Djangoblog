import json
from unittest.mock import patch

import cloudinary
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from blog.models import Category, Post
from content_ai.admin_editorial import (
    TemporaryVersionHistory,
    apply_suggestion_to_initial,
    preview_from_draft,
)
from content_ai.assistant.actions import (
    IMPLEMENTED_ACTIONS,
    get_action,
    is_action_implemented,
    list_actions_for_ui,
)
from content_ai.editorial.drafts import EditorialDraft
from content_ai.providers.exceptions import GenerationError
from content_ai.telemetry import AIExecutionTelemetry

User = get_user_model()


class AssistantActionRegistryTests(SimpleTestCase):
    def test_v1_only_generate_and_regenerate_are_implemented(self):
        self.assertEqual(IMPLEMENTED_ACTIONS, frozenset({'generate', 'regenerate'}))
        self.assertTrue(is_action_implemented('generate'))
        self.assertTrue(is_action_implemented('regenerate'))
        for action_id in (
            'rewrite',
            'shorter',
            'longer',
            'translate',
            'seo_optimize',
            'social_post',
        ):
            self.assertFalse(is_action_implemented(action_id))
            action = get_action(action_id)
            self.assertIsNotNone(action)
            self.assertFalse(action.enabled)

    def test_list_actions_for_ui_includes_placeholders(self):
        actions = list_actions_for_ui()
        ids = [item['id'] for item in actions]
        self.assertEqual(ids[0], 'generate')
        self.assertIn('rewrite', ids)
        self.assertIn('social_post', ids)
        rewrite = next(item for item in actions if item['id'] == 'rewrite')
        self.assertFalse(rewrite['enabled'])
        self.assertEqual(rewrite['coming_soon'], 'Coming soon')


class TemporaryVersionHistoryTests(SimpleTestCase):
    def test_keeps_last_three_versions(self):
        history = TemporaryVersionHistory(max_versions=3)
        history.add({'body': 'v1'})
        history.add({'body': 'v2'})
        history.add({'body': 'v3'})
        history.add({'body': 'v4'})
        self.assertEqual(len(history), 3)
        self.assertEqual([v['body'] for v in history.versions], ['v2', 'v3', 'v4'])
        self.assertEqual(history.active['body'], 'v4')

    def test_select_switches_active_version(self):
        history = TemporaryVersionHistory()
        history.add({'body': 'a'})
        history.add({'body': 'b'})
        history.add({'body': 'c'})
        selected = history.select(0)
        self.assertEqual(selected['body'], 'a')
        self.assertEqual(history.active['body'], 'a')

    def test_clear_resets_history(self):
        history = TemporaryVersionHistory()
        history.add({'body': 'a'})
        history.clear()
        self.assertEqual(len(history), 0)
        self.assertIsNone(history.active)


class ApplySuggestionTests(SimpleTestCase):
    def test_accept_payload_maps_to_admin_fields(self):
        """Use Draft maps preview fields onto Admin form initial data."""
        initial = apply_suggestion_to_initial(
            {},
            {
                'title': 'Accepted Title',
                'body': 'Accepted body',
                'summary': 'Accepted summary',
                'category_id': 9,
                'status': 0,
            },
        )
        self.assertEqual(initial['title'], 'Accepted Title')
        self.assertEqual(initial['content'], 'Accepted body')
        self.assertEqual(initial['excerpt'], 'Accepted summary')
        self.assertEqual(initial['category'], 9)
        self.assertEqual(initial['status'], 0)


@override_settings(
    CONTENT_AI_PROVIDER='mock',
    ADMIN_NOTIFICATION_ENABLED=False,
)
class AdminAIEditorialAssistantTests(TestCase):
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
        self.generate_url = reverse('admin:blog_post_ai_assistant_generate')
        self.add_url = reverse('admin:blog_post_add')

    def _login_staff(self):
        self.client.force_login(self.staff)

    def _generate_payload(self, **overrides):
        payload = {
            'action': 'generate',
            'title': 'Working title',
            'category_id': self.category.pk,
            'category': self.category.name,
            'language': 'sv',
            'context': 'Housing news',
            'instructions': 'Keep short',
            'post_id': '',
        }
        payload.update(overrides)
        return payload

    def test_anonymous_redirected(self):
        response = self.client.post(
            self.generate_url,
            data=json.dumps(self._generate_payload()),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn('/admin/login/', response.url)

    def test_non_staff_forbidden(self):
        user = User.objects.create_user(username='plain', password='password123')
        self.client.force_login(user)
        response = self.client.post(
            self.generate_url,
            data=json.dumps(self._generate_payload()),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 302)

    def test_staff_without_blog_permission_denied(self):
        bare_staff = User.objects.create_user(
            username='barestaff',
            password='password123',
            is_staff=True,
        )
        self.client.force_login(bare_staff)
        response = self.client.post(
            self.generate_url,
            data=json.dumps(self._generate_payload()),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 403)

    def test_button_visible_on_add(self):
        self._login_staff()
        response = self.client.get(self.add_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generate with AI')
        self.assertContains(response, 'ai-editorial-assistant')
        self.assertContains(response, self.generate_url)
        self.assertContains(response, 'Use Draft')
        self.assertContains(response, 'Coming soon')
        self.assertContains(response, 'data-ai-action="rewrite"')
        self.assertContains(response, 'data-ai-action="regenerate"')

    def test_button_visible_on_draft(self):
        self._login_staff()
        url = reverse('admin:blog_post_change', args=[self.draft.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Generate with AI')
        self.assertContains(response, f'data-post-id="{self.draft.pk}"')
        self.assertContains(response, 'Assistant Actions')

    def test_button_hidden_on_published(self):
        self._login_staff()
        url = reverse('admin:blog_post_change', args=[self.published.pk])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Generate with AI')
        self.assertNotContains(response, 'ai-editorial-assistant')

    def test_published_generate_blocked(self):
        self._login_staff()
        response = self.client.post(
            self.generate_url,
            data=json.dumps(self._generate_payload(post_id=self.published.pk)),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertIn('Draft', body['error']['message'])

    @patch('blog.admin.EditorialAIService.generate_draft')
    def test_generate_returns_preview_without_saving(self, mock_generate):
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
            data=json.dumps(self._generate_payload()),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        preview = data['preview']
        self.assertEqual(preview['title'], 'AI Suggested Title')
        self.assertEqual(preview['body'], 'AI suggested body content')
        self.assertEqual(preview['summary'], 'AI summary')
        self.assertEqual(preview['status'], 0)
        self.assertEqual(preview['category_id'], self.category.pk)
        self.assertIsNotNone(preview['telemetry'])
        self.assertEqual(Post.objects.count(), before)

    @patch('blog.admin.EditorialAIService.generate_draft')
    def test_regenerate_uses_service_again(self, mock_generate):
        mock_generate.side_effect = [
            EditorialDraft(title='V1', body='Body 1', summary='S1', language='sv'),
            EditorialDraft(title='V2', body='Body 2', summary='S2', language='sv'),
        ]
        self._login_staff()
        first = self.client.post(
            self.generate_url,
            data=json.dumps(self._generate_payload(action='generate')),
            content_type='application/json',
        )
        second = self.client.post(
            self.generate_url,
            data=json.dumps(self._generate_payload(action='regenerate')),
            content_type='application/json',
        )
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json()['preview']['body'], 'Body 1')
        self.assertEqual(second.json()['preview']['body'], 'Body 2')
        self.assertEqual(mock_generate.call_count, 2)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.content, 'Draft body')

    def test_future_action_rejected(self):
        self._login_staff()
        response = self.client.post(
            self.generate_url,
            data=json.dumps(self._generate_payload(action='rewrite')),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()['error']['code'], 'action_not_implemented')

    @patch('blog.admin.EditorialAIService.generate_draft')
    def test_generate_on_draft_does_not_overwrite_post(self, mock_generate):
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
            self.generate_url,
            data=json.dumps(
                self._generate_payload(
                    post_id=self.draft.pk,
                    title='Existing Draft Post',
                    language='fa',
                )
            ),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Post.objects.count(), before)
        self.draft.refresh_from_db()
        self.assertEqual(self.draft.content, 'Draft body')
        self.assertEqual(self.draft.status, 0)

    @patch('blog.admin.EditorialAIService.generate_draft')
    def test_provider_failure_keeps_no_persistence(self, mock_generate):
        mock_generate.side_effect = GenerationError('provider exploded')
        self._login_staff()
        before = Post.objects.count()
        response = self.client.post(
            self.generate_url,
            data=json.dumps(self._generate_payload()),
            content_type='application/json',
        )
        self.assertEqual(response.status_code, 502)
        self.assertIn('provider exploded', response.json()['error']['message'])
        self.assertEqual(Post.objects.count(), before)

    def test_preview_from_draft_helper(self):
        draft = EditorialDraft(
            title='',
            body='Body',
            summary='Summary',
            language='sv',
            metadata={'provider': 'mock'},
        )
        preview = preview_from_draft(
            draft,
            category_id=self.category.pk,
            request_values={'title': 'Fallback Title'},
        )
        self.assertEqual(preview['title'], 'Fallback Title')
        self.assertEqual(preview['body'], 'Body')
        self.assertEqual(preview['status'], 0)
