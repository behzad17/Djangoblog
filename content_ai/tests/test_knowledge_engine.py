"""Tests for inactive Knowledge Engine architecture (RFC-002)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from content_ai.config.ai_engine import (
    ENABLE_KNOWLEDGE_ENGINE,
    ENABLE_KNOWLEDGE_INJECTION,
    ENABLE_RAG,
    FEATURE_FLAGS,
)
from content_ai.knowledge.exceptions import (
    KnowledgeValidationError,
    ManifestError,
)
from content_ai.knowledge.injectors import KnowledgeInjector
from content_ai.knowledge.integration import apply_knowledge_if_enabled
from content_ai.knowledge.models import KnowledgeModule
from content_ai.knowledge.selectors import (
    KeywordSelector,
    get_knowledge_selector,
)
from content_ai.knowledge.utils.parser import (
    DEFAULT_KNOWLEDGE_ROOT,
    load_manifest,
    parse_knowledge_modules,
    validate_manifest,
)


class KnowledgeConfigFlagTests(unittest.TestCase):
    def test_all_knowledge_flags_disabled(self):
        self.assertFalse(ENABLE_KNOWLEDGE_ENGINE)
        self.assertFalse(ENABLE_RAG)
        self.assertFalse(ENABLE_KNOWLEDGE_INJECTION)
        self.assertFalse(FEATURE_FLAGS['ENABLE_KNOWLEDGE_ENGINE'])
        self.assertFalse(FEATURE_FLAGS['ENABLE_RAG'])
        self.assertFalse(FEATURE_FLAGS['ENABLE_KNOWLEDGE_INJECTION'])


class ManifestAndParserTests(unittest.TestCase):
    def test_manifest_loading(self):
        raw = load_manifest(DEFAULT_KNOWLEDGE_ROOT / 'manifest.yaml')
        self.assertIn('migration', raw)
        self.assertIn('healthcare', raw)
        self.assertEqual(raw['migration']['file'], 'migration.md')

    def test_parse_knowledge_modules(self):
        modules = parse_knowledge_modules()
        names = {m.name for m in modules}
        self.assertEqual(
            names,
            {
                'authorities',
                'migration',
                'healthcare',
                'education',
                'taxation',
                'labour_market',
                'glossary',
            },
        )
        migration = next(m for m in modules if m.name == 'migration')
        self.assertIsInstance(migration, KnowledgeModule)
        self.assertEqual(migration.title, 'Migration')
        self.assertIn('migration', migration.tags)
        self.assertTrue(migration.content.strip())

    def test_validate_manifest_success(self):
        raw = load_manifest(DEFAULT_KNOWLEDGE_ROOT / 'manifest.yaml')
        entries = validate_manifest(raw, DEFAULT_KNOWLEDGE_ROOT)
        self.assertEqual(len(entries), 7)

    def test_missing_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ManifestError):
                load_manifest(Path(tmp) / 'manifest.yaml')

    def test_missing_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = {
                'migration': {
                    'file': 'missing.md',
                    'title': 'Migration',
                    'tags': ['migration'],
                    'priority': 1,
                }
            }
            (root / 'manifest.yaml').write_text(
                yaml.safe_dump(manifest),
                encoding='utf-8',
            )
            with self.assertRaises(KnowledgeValidationError) as ctx:
                validate_manifest(manifest, root)
            self.assertIn('missing', str(ctx.exception).lower())

    def test_duplicate_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'a.md').write_text('a', encoding='utf-8')
            (root / 'b.md').write_text('b', encoding='utf-8')
            manifest = {
                'a': {
                    'file': 'a.md',
                    'title': 'A',
                    'tags': ['shared'],
                    'priority': 1,
                },
                'b': {
                    'file': 'b.md',
                    'title': 'B',
                    'tags': ['shared'],
                    'priority': 2,
                },
            }
            with self.assertRaises(KnowledgeValidationError) as ctx:
                validate_manifest(manifest, root)
            self.assertIn('Duplicate tag', str(ctx.exception))

    def test_invalid_metadata_priority(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'a.md').write_text('a', encoding='utf-8')
            manifest = {
                'a': {
                    'file': 'a.md',
                    'title': 'A',
                    'tags': ['a'],
                    'priority': 'high',
                }
            }
            with self.assertRaises(KnowledgeValidationError):
                validate_manifest(manifest, root)


class SelectorAndFactoryTests(unittest.TestCase):
    def test_keyword_selector_returns_empty(self):
        modules = parse_knowledge_modules()
        selected = KeywordSelector().select(
            'migration residence permit',
            style='news',
            language='fa',
            modules=modules,
        )
        self.assertEqual(selected, [])

    def test_factory_default(self):
        selector = get_knowledge_selector()
        self.assertIsInstance(selector, KeywordSelector)

    def test_factory_unknown(self):
        with self.assertRaises(ValueError):
            get_knowledge_selector('embedding')


class InjectorAndIntegrationTests(unittest.TestCase):
    def test_injector_returns_prompt_unchanged(self):
        prompt = '## User Prompt\n\nHello\n'
        modules = parse_knowledge_modules()
        self.assertEqual(
            KnowledgeInjector().inject(prompt, modules),
            prompt,
        )

    def test_integration_noop_while_flags_disabled(self):
        prompt = 'assembled prompt'
        self.assertEqual(
            apply_knowledge_if_enabled(
                prompt,
                user_prompt='healthcare',
                style='news',
                language='fa',
            ),
            prompt,
        )


class PromptBuilderUntouchedSmokeTests(unittest.TestCase):
    def test_prompt_builder_still_works_without_knowledge(self):
        from content_ai.prompts.builders import PromptBuilder

        prompt = PromptBuilder().build(user_prompt='short request')
        self.assertIn('## User Prompt', prompt)
        self.assertNotIn('## Knowledge', prompt)


if __name__ == '__main__':
    unittest.main()
