"""Tests for Editorial Workspace featured-image generation."""

from django.test import SimpleTestCase, TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from content_ai.editorial.image.prompt import build_featured_image_brief
from content_ai.editorial.image.style import category_visual_hint, content_type_visual
from content_ai.providers.mock import MOCK_IMAGE_DATA_URL
from content_ai.workspace.services import WorkspaceService
from content_ai.workspace.session import ArticleSections


class FeaturedImagePromptTests(SimpleTestCase):
    def test_requires_article_content(self):
        with self.assertRaises(ValueError):
            build_featured_image_brief(headline='', lead='', body='')

    def test_builds_from_persian_article_not_url(self):
        brief = build_featured_image_brief(
            headline='افزایش مالیات برای مستاجران',
            lead='سازمان مالیاتی قوانین جدیدی اعلام کرد.',
            body='جزئیات قانون شامل مهلت و مبلغ است. پلیس درگیر نیست.',
            content_type='news',
            goal='inform',
            category='Tax',
            tags=['skatt', 'housing'],
            publisher='SVT',
        )
        self.assertIn('16:9', brief.prompt)
        self.assertIn('NO readable text', brief.prompt)
        self.assertIn('افزایش مالیات', brief.prompt)
        self.assertNotIn('http://', brief.prompt)
        self.assertIn('tax documents', brief.prompt.lower())
        self.assertTrue(brief.explanation)

    def test_content_type_and_category_adaptation(self):
        self.assertIn('instructional', content_type_visual('guide').lower())
        self.assertIn('police', category_visual_hint(category='Police').lower())


@override_settings(CONTENT_AI_PROVIDER='mock')
class FeaturedImageWorkspaceTests(SimpleTestCase):
    def test_prepare_and_generate_does_not_touch_article(self):
        service = WorkspaceService()
        session = service.new_session()
        session.sections = ArticleSections(
            headline='عنوان فارسی',
            lead='لید خبر',
            body='بدنه کامل مقاله درباره مسکن در سوئد.',
            category='Housing',
            tags=['bostad'],
        )
        original_body = session.sections.body
        state = service.prepare_featured_image_prompt(session)
        self.assertEqual(state['status'], 'prompt_ready')
        self.assertIn('Peyvand', state['prompt'])
        edited = state['prompt'] + '\nExtra editor note: soft morning light.'
        generated = service.generate_featured_image(
            session,
            prompt=edited,
            regenerate=False,
        )
        self.assertEqual(generated['status'], 'generated')
        self.assertEqual(generated['image_url'], MOCK_IMAGE_DATA_URL)
        self.assertEqual(session.sections.body, original_body)

        regenerated = service.generate_featured_image(
            session,
            prompt=edited + ' Calm street.',
            regenerate=True,
        )
        self.assertEqual(regenerated['status'], 'generated')
        self.assertTrue(regenerated['previous_prompt'])
        self.assertEqual(session.sections.body, original_body)
        self.assertTrue(session.pipeline.get('image_ready'))

    def test_use_previous_prompt(self):
        service = WorkspaceService()
        session = service.new_session()
        session.sections = ArticleSections(
            headline='مصاحبه',
            lead='گفتگو',
            body='متن مصاحبه',
        )
        service.prepare_featured_image_prompt(session)
        first = session.metadata['featured_image']['prompt']
        service.generate_featured_image(session, prompt=first, regenerate=False)
        service.generate_featured_image(
            session,
            prompt=first + ' v2',
            regenerate=True,
        )
        restored = service.use_previous_image_prompt(session)
        self.assertEqual(restored['prompt'], first)
        self.assertEqual(restored['previous_prompt'], first + ' v2')


@override_settings(
    CONTENT_AI_PROVIDER='mock',
    ROOT_URLCONF='codestar.urls',
)
class FeaturedImageApiTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='imgstaff',
            password='pass',
            is_staff=True,
        )
        self.client.force_login(self.user)

    def test_prepare_image_prompt_api(self):
        # Seed session via reset + update_sections
        self.client.post(reverse('content_ai:workspace_api', kwargs={'action': 'reset'}))
        resp = self.client.post(
            reverse('content_ai:workspace_api', kwargs={'action': 'update_sections'}),
            data='{"sections":{"headline":"عنوان","lead":"لید","body":"بدنه مقاله"}}',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        resp = self.client.post(
            reverse(
                'content_ai:workspace_api',
                kwargs={'action': 'prepare_image_prompt'},
            ),
            data='{"sections":{"headline":"عنوان","lead":"لید","body":"بدنه مقاله"}}',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload['ok'])
        self.assertIn('prompt', payload['featured_image'])

    def test_generate_image_api_with_mock(self):
        self.client.post(reverse('content_ai:workspace_api', kwargs={'action': 'reset'}))
        self.client.post(
            reverse('content_ai:workspace_api', kwargs={'action': 'update_sections'}),
            data='{"sections":{"headline":"عنوان","lead":"لید","body":"بدنه"}}',
            content_type='application/json',
        )
        resp = self.client.post(
            reverse(
                'content_ai:workspace_api',
                kwargs={'action': 'generate_image'},
            ),
            data='{"sections":{"headline":"عنوان","lead":"لید","body":"بدنه"},"prompt":""}',
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200, resp.content)
        payload = resp.json()
        self.assertTrue(payload['ok'])
        self.assertEqual(
            payload['featured_image']['image_url'],
            MOCK_IMAGE_DATA_URL,
        )
        # Article body unchanged in session payload
        self.assertEqual(
            payload['session']['sections']['body'],
            'بدنه',
        )
