"""Tests for Editorial Workspace featured-image pipeline v1."""

from unittest.mock import MagicMock, patch

from django.test import SimpleTestCase, TestCase, override_settings
from django.contrib.auth import get_user_model
from django.urls import reverse

from content_ai.editorial.image.attach import (
    extract_cloudinary_public_id,
    resolve_featured_image_public_id,
)
from content_ai.editorial.image.planner import plan_featured_image
from content_ai.editorial.image.prompt import build_featured_image_brief
from content_ai.editorial.image.style import (
    DEFAULT_IMAGE_STYLE,
    category_visual_hint,
    content_type_visual,
    resolve_image_style,
)
from content_ai.providers.mock import MOCK_IMAGE_DATA_URL
from content_ai.workspace.services import WorkspaceService
from content_ai.workspace.session import ArticleSections


class FeaturedImagePromptTests(SimpleTestCase):
    def test_requires_article_content(self):
        with self.assertRaises(ValueError):
            build_featured_image_brief(headline='', lead='', body='')

    def test_rejects_title_alone(self):
        with self.assertRaises(ValueError):
            build_featured_image_brief(
                headline='فقط عنوان',
                lead='',
                body='',
            )

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
            image_style='editorial_photo',
        )
        self.assertEqual(brief.image_style, 'editorial_photo')
        self.assertIsNotNone(brief.plan)
        self.assertIn('16:9', brief.prompt)
        self.assertIn('never include', brief.prompt.lower())
        self.assertIn('typography', brief.prompt.lower())
        self.assertIn('افزایش مالیات', brief.prompt)
        self.assertNotIn('http://', brief.prompt)
        self.assertIn('tax', brief.prompt.lower())
        self.assertTrue(brief.explanation)
        # Planner is internal — plan exists but UI must not show it.
        plan_dict = brief.plan_dict()
        self.assertIn('primary_visual_subject', plan_dict)
        self.assertIn('main_subject', plan_dict)  # compatibility alias
        self.assertIn('tax', plan_dict['primary_subject'].lower())

    def test_illustration_style(self):
        brief = build_featured_image_brief(
            headline='راهنمای ثبت‌نام',
            lead='مراحل ساده برای شروع.',
            body='گام اول و دوم را دنبال کنید.',
            content_type='guide',
            image_style='editorial_illustration',
        )
        self.assertEqual(brief.image_style, 'editorial_illustration')
        self.assertIn('illustration', brief.prompt.lower())

    def test_content_type_and_category_adaptation(self):
        self.assertIn('educational', content_type_visual('guide').lower())
        self.assertIn('police', category_visual_hint(category='Police').lower())
        self.assertEqual(resolve_image_style(None), DEFAULT_IMAGE_STYLE)


class ImagePlannerV2Tests(SimpleTestCase):
    def test_constitution_article_plans_parliament_not_lifestyle(self):
        plan = plan_featured_image(
            headline='بررسی قوانین اساسی و آیین‌نامه پارلمان سوئد',
            lead=(
                'قوانین اساسی و آیین‌نامه پارلمان سوئد نقش بنیادینی در نظام '
                'حکمرانی این کشور ایفا می‌کنند.'
            ),
            body=(
                'چهار ستون قانون اساسی سوئد شامل قانون حکومت، آزادی مطبوعات، '
                'آزادی بیان و قانون جانشینی سلطنت است. ریکسداگ عالی‌ترین مظهر '
                'اراده مردم است.'
            ),
            content_type='report',
            category='سوئد امروز',
            tags=['قانون اساسی', 'سوئد', 'ریکسداگ', 'دموکراسی'],
        )
        visual = plan.primary_visual_subject.lower()
        self.assertIn('parliament', visual)
        self.assertIn('riksdag', plan.location.lower())
        self.assertNotIn('grocer', visual)
        self.assertNotIn('elderly', visual)
        self.assertNotIn('conversation', visual)
        self.assertNotIn('helping', visual)
        avoid_blob = ' '.join(plan.avoid).lower()
        self.assertIn('lifestyle', avoid_blob)
        self.assertIn('elderly', avoid_blob)
        self.assertIn('shopping', avoid_blob)

        brief = build_featured_image_brief(
            headline='بررسی قوانین اساسی و آیین‌نامه پارلمان سوئد',
            lead='قوانین اساسی و آیین‌نامه پارلمان سوئد نقش بنیادینی دارند.',
            body='ریکسداگ و قانون اساسی سوئد.',
            content_type='report',
            category='سوئد امروز',
            tags=['قانون اساسی', 'ریکسداگ'],
            plan=plan,
        )
        prompt_l = brief.prompt.lower()
        self.assertIn('primary visual subject', prompt_l)
        self.assertIn('parliament', prompt_l)
        self.assertIn('front-page', prompt_l)
        self.assertNotIn('friendly conversation', prompt_l)
        self.assertNotIn('helping each other', prompt_l)

    def test_tax_article_plans_authority_not_coffee_lifestyle(self):
        plan = plan_featured_image(
            headline='افزایش مالیات برای مستاجران',
            lead='سازمان مالیاتی قوانین جدیدی اعلام کرد.',
            body='جزئیات قانون شامل مهلت و مبلغ است.',
            content_type='news',
            category='Tax',
            tags=['skatt'],
        )
        self.assertIn('tax', plan.primary_subject.lower())
        self.assertNotIn('coffee', plan.primary_visual_subject.lower())
        self.assertTrue(plan.avoid)

    def test_housing_article_plans_building(self):
        plan = plan_featured_image(
            headline='مسکن در استکهلم',
            lead='اجاره افزایش یافته است.',
            body='خانواده‌ها به دنبال آپارتمان هستند.',
            content_type='news',
            category='Housing',
            tags=['bostad'],
        )
        self.assertIn('residential', plan.primary_visual_subject.lower())
        self.assertEqual(plan.primary_subject, 'Housing')
        self.assertNotIn('fantasy', plan.primary_visual_subject.lower())

    def test_planner_json_shape(self):
        plan = plan_featured_image(
            headline='پلیس استکهلم گزارش داد',
            lead='نیروی پلیس عملیات آرامی انجام داد.',
            body='جزئیات در ایستگاه پلیس اعلام شد.',
            content_type='news',
        )
        data = plan.to_dict()
        for key in (
            'primary_subject',
            'primary_visual_subject',
            'location',
            'secondary_elements',
            'visual_style',
            'mood',
            'avoid',
        ):
            self.assertIn(key, data)
        self.assertIsInstance(data['secondary_elements'], list)
        self.assertIsInstance(data['avoid'], list)
        self.assertLessEqual(len(data['secondary_elements']), 2)


@override_settings(CONTENT_AI_PROVIDER='mock')
class FeaturedImageWorkspaceTests(SimpleTestCase):
    def test_generate_draft_auto_prepares_image_prompt(self):
        editorial = MagicMock()
        from content_ai.editorial.drafts import EditorialDraft

        editorial.generate_draft.return_value = EditorialDraft(
            title='عنوان فارسی',
            lead='لید خبر درباره مسکن',
            body='بدنه کامل مقاله درباره مسکن در سوئد و جزئیات بیشتر.',
            summary='خلاصه',
            language='fa',
            metadata={},
        )
        service = WorkspaceService(editorial=editorial)
        session = service.new_session()
        session.source_material = 'Source article with enough text for generation.'
        session.metadata['source_binding'] = {
            'session_id': session.session_id,
            'source_url': '',
            'source_text_sha256': __import__('hashlib')
            .sha256(session.source_material.encode())
            .hexdigest(),
            'source_text_chars': len(session.source_material),
            'retrieval': 'manual_paste',
        }
        service.generate_draft(session, title='عنوان')
        featured = session.metadata.get('featured_image') or {}
        self.assertTrue((featured.get('prompt') or '').strip())
        self.assertEqual(featured.get('status'), 'prompt_ready')
        self.assertTrue(featured.get('auto_prepared'))
        self.assertIn(
            'Featured image prompt prepared automatically',
            ' '.join(session.last_explanations),
        )

    def test_prepare_and_generate_does_not_touch_article(self):
        service = WorkspaceService()
        session = service.new_session()
        session.sections = ArticleSections(
            headline='عنوان فارسی',
            lead='لید خبر',
            body='بدنه کامل مقاله درباره مسکن در سوئد.',
            category='Housing',
            tags=['bostad'],
            summary='خلاصه',
        )
        original_body = session.sections.body
        original_summary = session.sections.summary
        original_category = session.sections.category
        state = service.prepare_featured_image_prompt(session)
        self.assertEqual(state['status'], 'prompt_ready')
        self.assertEqual(state['image_style'], 'editorial_photo')
        self.assertNotIn('planner', state)
        self.assertIn('Peyvand', state['prompt'])
        self.assertTrue(state['original_prompt'])
        # Internal planner stored on session but stripped from public state
        self.assertIn('planner', session.metadata['featured_image'])

        edited = state['prompt'] + '\nExtra editor note: soft morning light.'
        generated = service.generate_featured_image(
            session,
            prompt=edited,
            regenerate=False,
        )
        self.assertEqual(generated['status'], 'generated')
        self.assertEqual(generated['image_url'], MOCK_IMAGE_DATA_URL)
        self.assertEqual(session.sections.body, original_body)
        self.assertEqual(session.sections.summary, original_summary)
        self.assertEqual(session.sections.category, original_category)

        regenerated = service.generate_featured_image(
            session,
            prompt=edited + ' Calm street.',
            regenerate=True,
        )
        self.assertEqual(regenerated['status'], 'generated')
        self.assertTrue(regenerated['previous_prompt'])
        self.assertTrue(regenerated.get('pending_accept'))
        self.assertEqual(session.sections.body, original_body)
        self.assertEqual(session.sections.summary, original_summary)
        self.assertEqual(session.sections.category, original_category)
        self.assertTrue(session.pipeline.get('image_ready'))

    def test_restore_original_prompt(self):
        service = WorkspaceService()
        session = service.new_session()
        session.sections = ArticleSections(
            headline='مصاحبه',
            lead='گفتگو',
            body='متن مصاحبه',
        )
        service.prepare_featured_image_prompt(session)
        original = session.metadata['featured_image']['original_prompt']
        session.metadata['featured_image']['prompt'] = original + ' edited'
        restored = service.restore_original_image_prompt(session)
        self.assertEqual(restored['prompt'], original)

    def test_change_style_rebuilds_prompt(self):
        service = WorkspaceService()
        session = service.new_session()
        session.sections = ArticleSections(
            headline='فناوری',
            lead='ابزارهای جدید',
            body='توضیح کامل درباره فناوری.',
            category='Technology',
        )
        service.prepare_featured_image_prompt(session)
        photo_prompt = session.metadata['featured_image']['prompt']
        updated = service.set_featured_image_style(
            session,
            image_style='editorial_illustration',
        )
        self.assertEqual(updated['image_style'], 'editorial_illustration')
        self.assertNotEqual(updated['prompt'], photo_prompt)
        self.assertIn('illustration', updated['prompt'].lower())

    @patch('content_ai.workspace.services.upload_featured_image_asset')
    @patch('content_ai.workspace.services.attach_featured_image_to_post')
    def test_accept_attaches_to_draft(self, mock_attach, mock_upload):
        mock_upload.return_value = {
            'public_id': 'peyvand/editorial/featured/test',
            'secure_url': 'https://res.cloudinary.com/demo/image/upload/test.png',
        }
        mock_attach.return_value = MagicMock(pk=42)

        service = WorkspaceService()
        session = service.new_session()
        session.sections = ArticleSections(
            headline='عنوان',
            lead='لید',
            body='بدنه مقاله',
            category='News',
        )
        service.prepare_featured_image_prompt(session)
        service.generate_featured_image(session)

        user = MagicMock()
        user.is_authenticated = True
        user.username = 'editor'
        user.pk = 1

        with patch.object(
            service,
            'save_blog_draft',
            return_value={'post_id': 42, 'title': 'عنوان', 'created': True},
        ), patch('blog.models.Post.objects.get') as mock_get:
            post = MagicMock(pk=42)
            post.featured_image = MagicMock(public_id='peyvand/editorial/featured/test')
            mock_get.return_value = post
            # attach is mocked; simulate persisted public_id on refresh.
            def _attach(p, *, public_id):
                p.featured_image = MagicMock(public_id=public_id)
                return p

            mock_attach.side_effect = _attach
            result = service.accept_featured_image(session, user=user)

        self.assertTrue(result['accepted'])
        self.assertEqual(result['status'], 'accepted')
        self.assertEqual(
            result['cloudinary_public_id'],
            'peyvand/editorial/featured/test',
        )
        self.assertGreaterEqual(mock_attach.call_count, 1)
        self.assertNotEqual(
            session.metadata['featured_image'].get('cloudinary_public_id'),
            '',
        )


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
            data=(
                '{"sections":{"headline":"عنوان","lead":"لید","body":"بدنه مقاله"},'
                '"image_style":"editorial_photo"}'
            ),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload['ok'])
        self.assertIn('prompt', payload['featured_image'])
        self.assertNotIn('planner', payload['featured_image'])
        self.assertNotIn(
            'planner',
            (payload['session'].get('metadata') or {})
            .get('featured_image', {}),
        )

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
        self.assertEqual(
            payload['session']['sections']['body'],
            'بدنه',
        )


class CloudinaryPublicIdHelperTests(SimpleTestCase):
    def test_extract_from_delivery_url(self):
        url = (
            'https://res.cloudinary.com/demo/image/upload/v1785091045/'
            'peyvand/editorial/featured/abc123.png'
        )
        self.assertEqual(
            extract_cloudinary_public_id(url),
            'peyvand/editorial/featured/abc123',
        )

    def test_resolve_prefers_explicit_public_id(self):
        pid = resolve_featured_image_public_id(
            {
                'cloudinary_public_id': 'peyvand/editorial/featured/x',
                'image_url': 'https://res.cloudinary.com/demo/image/upload/v1/other.png',
            }
        )
        self.assertEqual(pid, 'peyvand/editorial/featured/x')


@override_settings(CONTENT_AI_PROVIDER='mock')
class FeaturedImagePersistIntegrationTests(TestCase):
    def setUp(self):
        User = get_user_model()
        from blog.models import Category

        self.user = User.objects.create_user(
            username='imgpersist',
            password='pass',
            is_staff=True,
        )
        Category.objects.get_or_create(
            slug='news',
            defaults={'name': 'News'},
        )

    @patch('content_ai.workspace.services.upload_featured_image_asset')
    def test_generate_accept_save_draft_sets_post_featured_image(self, mock_upload):
        from blog.models import Post

        public_id = 'peyvand/editorial/featured/integration-test'
        secure_url = (
            f'https://res.cloudinary.com/demo/image/upload/v1/{public_id}.png'
        )
        mock_upload.return_value = {
            'public_id': public_id,
            'secure_url': secure_url,
        }

        service = WorkspaceService()
        session = service.new_session()
        session.sections = ArticleSections(
            headline='عنوان ادغام تصویر',
            lead='لید خبر',
            body='بدنه مقاله برای ذخیره پیش‌نویس.',
            category='News',
            tags=['test'],
        )
        service.prepare_featured_image_prompt(session)
        generated = service.generate_featured_image(session)
        self.assertEqual(generated['status'], 'generated')

        accepted = service.accept_featured_image(session, user=self.user)
        self.assertTrue(accepted['accepted'])
        self.assertEqual(accepted['cloudinary_public_id'], public_id)

        post_id = accepted['blog_draft']['post_id']
        post = Post.objects.get(pk=post_id)
        stored = (
            getattr(post.featured_image, 'public_id', None)
            or str(post.featured_image)
        )
        self.assertNotEqual(stored, 'placeholder')
        self.assertEqual(stored, public_id)

        # Save Draft again must keep the image (not reset to placeholder).
        saved = service.save_blog_draft(session, user=self.user)
        self.assertEqual(saved['post_id'], post_id)
        post.refresh_from_db()
        stored_after = (
            getattr(post.featured_image, 'public_id', None)
            or str(post.featured_image)
        )
        self.assertNotEqual(stored_after, 'placeholder')
        self.assertEqual(stored_after, public_id)
