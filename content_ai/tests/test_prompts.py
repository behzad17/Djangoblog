from django.test import SimpleTestCase

from content_ai.constants import AIGenerationTask
from content_ai.prompts import (
    AdPromptTemplate,
    BasePromptTemplate,
    PostPromptTemplate,
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

    def test_get_prompt_template_for_ad(self):
        template = get_prompt_template(AIGenerationTask.AD_GENERATION)
        self.assertIsInstance(template, AdPromptTemplate)

    def test_unregistered_task_raises(self):
        with self.assertRaises(GenerationError) as ctx:
            get_prompt_template(AIGenerationTask.REWRITE)
        self.assertIn('rewrite', str(ctx.exception).lower())


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
        self.assertIsInstance(prompt, str)

    def test_post_prompt_build_with_none_uses_defaults(self):
        prompt = PostPromptTemplate().build(None)
        self.assertIn('Task: POST_GENERATION', prompt)
        self.assertIn('Title: ', prompt)
