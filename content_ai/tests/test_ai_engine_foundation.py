"""Tests for inactive AI Engine prompt architecture (RFC-001).

Does not exercise production OpenAI or AssetPromptTemplate paths.
"""

from __future__ import annotations

import shutil
import tempfile
import unittest
from pathlib import Path

from content_ai.config.ai_engine import (
    DEFAULT_PROMPT_VERSION,
    DEFAULT_STYLE,
    FEATURE_FLAGS,
    SUPPORTED_PROMPT_VERSIONS,
    SUPPORTED_STYLES,
)
from content_ai.prompts.builders import (
    InvalidPromptStructureError,
    MissingPromptModuleError,
    PromptBuilder,
    UnknownPromptVersionError,
    UnknownStyleError,
)
from content_ai.prompts.validators import (
    REQUIRED_SECTION_ORDER,
    SECTION_AUDIENCE,
    SECTION_IDENTITY,
    SECTION_OUTPUT_SCHEMA,
    SECTION_STYLE,
    SECTION_USER_PROMPT,
    SECTION_WRITING,
    PromptValidator,
)
from content_ai.telemetry.generation_metrics import build_generation_metrics
from content_ai.telemetry.prompt_versions import record_prompt_version


def _repo_prompts_root() -> Path:
    return Path(__file__).resolve().parents[1] / 'prompts'


class AIEngineConfigTests(unittest.TestCase):
    def test_defaults_and_supported_sets(self):
        self.assertEqual(DEFAULT_PROMPT_VERSION, 'v1')
        self.assertEqual(DEFAULT_STYLE, 'news')
        self.assertIn('v1', SUPPORTED_PROMPT_VERSIONS)
        self.assertEqual(
            set(SUPPORTED_STYLES),
            {'news', 'analysis', 'educational', 'friendly'},
        )
        self.assertFalse(FEATURE_FLAGS['use_ai_engine_prompt_builder'])


class PromptValidatorSuccessTests(unittest.TestCase):
    def setUp(self):
        self.validator = PromptValidator(prompts_root=_repo_prompts_root())

    def test_validate_version_v1(self):
        self.validator.validate_version('v1')

    def test_validate_style_news(self):
        self.validator.validate_style('news', version='v1')

    def test_validate_required_files_v1_news(self):
        self.validator.validate_required_files('v1', 'news')

    def test_validate_assembled_prompt_order(self):
        prompt = '\n'.join(
            f'{header}\nbody'
            for header in REQUIRED_SECTION_ORDER
        )
        self.validator.validate_assembled_prompt(prompt)


class PromptValidatorFailureTests(unittest.TestCase):
    def setUp(self):
        self.validator = PromptValidator(prompts_root=_repo_prompts_root())

    def test_unknown_version(self):
        with self.assertRaises(UnknownPromptVersionError):
            self.validator.validate_version('v999')

    def test_unknown_style(self):
        with self.assertRaises(UnknownStyleError):
            self.validator.validate_style('sarcastic')

    def test_missing_style_file_for_known_name_wrong_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'v1' / 'system').mkdir(parents=True)
            (root / 'v1' / 'styles').mkdir(parents=True)
            for name in (
                'identity.md',
                'audience.md',
                'writing.md',
                'output_schema.md',
            ):
                (root / 'v1' / 'system' / name).write_text('x', encoding='utf-8')
            validator = PromptValidator(prompts_root=root)
            with self.assertRaises(UnknownStyleError):
                validator.validate_style('news', version='v1')

    def test_missing_module_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'v1' / 'system').mkdir(parents=True)
            (root / 'v1' / 'styles').mkdir(parents=True)
            (root / 'v1' / 'styles' / 'news.md').write_text('s', encoding='utf-8')
            for name in ('identity.md', 'audience.md', 'writing.md'):
                (root / 'v1' / 'system' / name).write_text('x', encoding='utf-8')
            # output_schema.md intentionally missing
            validator = PromptValidator(prompts_root=root)
            with self.assertRaises(MissingPromptModuleError):
                validator.validate_required_files('v1', 'news')

    def test_invalid_prompt_structure_wrong_order(self):
        prompt = (
            f'{SECTION_AUDIENCE}\na\n'
            f'{SECTION_IDENTITY}\nb\n'
            f'{SECTION_WRITING}\nc\n'
            f'{SECTION_STYLE}\nd\n'
            f'{SECTION_OUTPUT_SCHEMA}\ne\n'
            f'{SECTION_USER_PROMPT}\nf\n'
        )
        with self.assertRaises(InvalidPromptStructureError):
            self.validator.validate_assembled_prompt(prompt)

    def test_invalid_prompt_structure_missing_section(self):
        with self.assertRaises(InvalidPromptStructureError):
            self.validator.validate_assembled_prompt(
                f'{SECTION_IDENTITY}\nonly\n'
            )

    def test_knowledge_section_rejected(self):
        prompt = '\n'.join(
            f'{header}\nbody'
            for header in REQUIRED_SECTION_ORDER
        ) + '\n## Knowledge\nnope\n'
        with self.assertRaises(InvalidPromptStructureError):
            self.validator.validate_assembled_prompt(prompt)

    def test_empty_module_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / 'empty.md'
            path.write_text('   \n', encoding='utf-8')
            validator = PromptValidator(prompts_root=root)
            with self.assertRaises(InvalidPromptStructureError):
                validator.validate_module_non_empty(path, 'empty')


class PromptBuilderTests(unittest.TestCase):
    def setUp(self):
        self.builder = PromptBuilder(prompts_root=_repo_prompts_root())

    def test_builder_success_default_v1_news(self):
        prompt = self.builder.build(user_prompt='Write a short housing update.')
        self.assertIn(SECTION_IDENTITY, prompt)
        self.assertIn(SECTION_AUDIENCE, prompt)
        self.assertIn(SECTION_WRITING, prompt)
        self.assertIn(SECTION_STYLE, prompt)
        self.assertIn(SECTION_OUTPUT_SCHEMA, prompt)
        self.assertIn(SECTION_USER_PROMPT, prompt)
        self.assertIn('Write a short housing update.', prompt)
        self.assertNotIn('## Knowledge', prompt)

    def test_prompt_ordering(self):
        prompt = self.builder.build(
            version='v1',
            style='analysis',
            user_prompt='Explain the topic.',
        )
        positions = [prompt.find(h) for h in REQUIRED_SECTION_ORDER]
        self.assertTrue(all(p >= 0 for p in positions))
        self.assertEqual(positions, sorted(positions))

    def test_style_loading_each_supported_style(self):
        for style in SUPPORTED_STYLES:
            prompt = self.builder.build(style=style, user_prompt='x')
            self.assertIn(SECTION_STYLE, prompt)

    def test_version_loading_v1(self):
        prompt = self.builder.build(version='v1', user_prompt='x')
        self.assertTrue(prompt.startswith(SECTION_IDENTITY))

    def test_unknown_version(self):
        with self.assertRaises(UnknownPromptVersionError):
            self.builder.build(version='v2', user_prompt='x')

    def test_unknown_style(self):
        with self.assertRaises(UnknownStyleError):
            self.builder.build(style='unknown-style', user_prompt='x')

    def test_missing_prompt_file(self):
        src = _repo_prompts_root() / 'v1'
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            shutil.copytree(src, root / 'v1')
            (root / 'v1' / 'system' / 'identity.md').unlink()
            builder = PromptBuilder(prompts_root=root)
            with self.assertRaises(MissingPromptModuleError):
                builder.build(user_prompt='x')

    def test_prompt_loading_includes_module_titles(self):
        prompt = self.builder.build(style='educational', user_prompt='teach')
        self.assertIn('Identity', prompt)
        self.assertIn('Educational', prompt)


class ExistingTelemetryImportSmokeTests(unittest.TestCase):
    """Ensure package conversion did not break production telemetry imports."""

    def test_ai_execution_telemetry_still_importable(self):
        from content_ai.telemetry import (
            AIExecutionTelemetry,
            attach_telemetry,
            merge_telemetry,
            utc_now,
        )

        self.assertTrue(callable(utc_now))
        self.assertTrue(callable(merge_telemetry))
        self.assertTrue(callable(attach_telemetry))
        self.assertEqual(AIExecutionTelemetry().provider, '')

    def test_engine_telemetry_placeholders(self):
        record = record_prompt_version('v1', 'news')
        self.assertEqual(record.prompt_version, 'v1')
        metrics = build_generation_metrics(model='test', success=True)
        self.assertEqual(metrics.model, 'test')
        self.assertTrue(metrics.success)


class KnowledgeAndConfigLayoutTests(unittest.TestCase):
    def test_knowledge_placeholders_exist(self):
        root = Path(__file__).resolve().parents[1] / 'knowledge'
        for name in ('sweden', 'community', 'peyvand', 'templates'):
            self.assertTrue((root / name).is_dir(), msg=name)
        self.assertTrue((root / 'manifest.yaml').is_file())
        self.assertTrue(
            (root / 'sweden' / 'authorities' / 'Skatteverket.md').is_file()
        )
        self.assertTrue(
            (root / 'peyvand' / 'terminology' / 'glossary.md').is_file()
        )

    def test_system_and_style_placeholders_exist(self):
        root = _repo_prompts_root() / 'v1'
        for name in (
            'system/identity.md',
            'system/audience.md',
            'system/writing.md',
            'system/output_schema.md',
            'styles/news.md',
            'styles/analysis.md',
            'styles/educational.md',
            'styles/friendly.md',
        ):
            self.assertTrue((root / name).is_file(), msg=name)


if __name__ == '__main__':
    unittest.main()
