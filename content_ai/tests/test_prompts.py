from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import SimpleTestCase

from content_ai.constants import AIGenerationTask
from content_ai.prompts import (
    AdPromptTemplate,
    AssetPromptTemplate,
    BasePromptTemplate,
    PostPromptTemplate,
    PromptLoader,
    PromptTemplateNotFound,
    TemplateRenderer,
    get_prompt_template,
    list_prompt_tasks,
)
from content_ai.providers.exceptions import GenerationError
from content_ai.schemas import AdGenerationRequest, PostGenerationRequest


class PromptRegistryTests(SimpleTestCase):
    def test_list_prompt_tasks_includes_post_and_ad(self):
        self.assertEqual(
            set(list_prompt_tasks()),
            {
                AIGenerationTask.POST_GENERATION,
                AIGenerationTask.AD_GENERATION,
            },
        )

    def test_get_prompt_template_for_post(self):
        template = get_prompt_template(AIGenerationTask.POST_GENERATION)
        self.assertIsInstance(template, PostPromptTemplate)
        self.assertIsInstance(template, BasePromptTemplate)
        self.assertIsInstance(template, AssetPromptTemplate)

    def test_get_prompt_template_for_ad(self):
        template = get_prompt_template(AIGenerationTask.AD_GENERATION)
        self.assertIsInstance(template, AdPromptTemplate)

    def test_unregistered_task_raises(self):
        with self.assertRaises(GenerationError) as ctx:
            get_prompt_template(AIGenerationTask.REWRITE)
        self.assertIn('rewrite', str(ctx.exception).lower())

    def test_get_prompt_template_version_selection(self):
        template = get_prompt_template(
            AIGenerationTask.POST_GENERATION,
            version='v1',
        )
        self.assertEqual(template.version, 'v1')


class PromptLoaderTests(SimpleTestCase):
    def test_loads_post_v1_markdown(self):
        text = PromptLoader().load('post', 'v1')
        self.assertIn('POST_GENERATION', text)
        self.assertIn('{{ title }}', text)
        self.assertIn('{{ instructions }}', text)

    def test_loads_ads_v1_markdown(self):
        text = PromptLoader().load('ads', 'v1')
        self.assertIn('AD_GENERATION', text)
        self.assertIn('{{ business_name }}', text)

    def test_missing_template_raises(self):
        with self.assertRaises(PromptTemplateNotFound) as ctx:
            PromptLoader().load('post', 'v999')
        self.assertIn('v999', str(ctx.exception))

    def test_version_selection_from_custom_root(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'post').mkdir()
            (root / 'post' / 'v2.md').write_text(
                'Version two for {{ title }}\n',
                encoding='utf-8',
            )
            loader = PromptLoader(base_dir=root)
            self.assertTrue(loader.exists('post', 'v2'))
            self.assertEqual(
                loader.load('post', 'v2').strip(),
                'Version two for {{ title }}',
            )
            with self.assertRaises(PromptTemplateNotFound):
                loader.load('post', 'v1')


class TemplateRendererTests(SimpleTestCase):
    def test_placeholder_replacement(self):
        rendered = TemplateRenderer().render(
            'Hello {{ title }} ({{ language }})',
            {'title': 'Housing', 'language': 'sv'},
        )
        self.assertEqual(rendered, 'Hello Housing (sv)')

    def test_missing_placeholder_becomes_empty(self):
        rendered = TemplateRenderer().render('X={{ missing }}Y', {})
        self.assertEqual(rendered, 'X=Y')

    def test_whitespace_inside_braces(self):
        rendered = TemplateRenderer().render(
            '{{  title  }}',
            {'title': 'Ok'},
        )
        self.assertEqual(rendered, 'Ok')


class PromptBuilderTests(SimpleTestCase):
    def test_post_prompt_includes_request_fields(self):
        request = PostGenerationRequest(
            title='Housing',
            source='editorial',
            language='sv',
            category='news',
            context='local',
            instructions='formal',
        )
        prompt = PostPromptTemplate().build(request)
        self.assertIn('Task: POST_GENERATION', prompt)
        self.assertIn('Title: Housing', prompt)
        self.assertIn('Language: sv', prompt)
        self.assertIn('Instructions: formal', prompt)
        self.assertNotIn('{{', prompt)
        self.assertIsInstance(prompt, str)

    def test_ad_prompt_includes_request_fields(self):
        request = AdGenerationRequest(
            business_name='Cafe',
            category='food',
            language='fa',
            city='Stockholm',
            description='Lunch',
            target_audience='locals',
            instructions='short',
        )
        prompt = AdPromptTemplate().build(request)
        self.assertIn('Task: AD_GENERATION', prompt)
        self.assertIn('Business name: Cafe', prompt)
        self.assertIn('City: Stockholm', prompt)
        self.assertIn('Target audience: locals', prompt)
        self.assertNotIn('{{', prompt)
        self.assertIsInstance(prompt, str)

    def test_post_prompt_build_with_none_uses_defaults(self):
        prompt = PostPromptTemplate().build(None)
        self.assertIn('Task: POST_GENERATION', prompt)
        self.assertIn('Title: ', prompt)

    def test_post_prompt_python_has_no_large_inline_body(self):
        source = Path(PostPromptTemplate.__module__.replace('.', '/') + '.py')
        # Resolve via import file path instead.
        import content_ai.prompts.post as post_mod

        text = Path(post_mod.__file__).read_text(encoding='utf-8')
        self.assertNotIn('You are a Peyvand content assistant', text)

    def test_versioned_template_via_loader(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'post').mkdir()
            (root / 'post' / 'v2.md').write_text(
                'ALT {{ title }}\n',
                encoding='utf-8',
            )
            template = PostPromptTemplate(
                version='v2',
                loader=PromptLoader(base_dir=root),
            )
            prompt = template.build(PostGenerationRequest(title='Hello'))
            self.assertEqual(prompt.strip(), 'ALT Hello')
