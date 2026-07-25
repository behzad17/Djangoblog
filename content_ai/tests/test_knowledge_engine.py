"""Tests for Editorial Knowledge Base (RFC-002.5) + Knowledge Engine."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

import yaml

from content_ai.config.ai_engine import (
    ENABLE_KNOWLEDGE_ENGINE,
    ENABLE_KNOWLEDGE_INJECTION,
    ENABLE_RAG,
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
    extract_glossary_terms,
    load_manifest,
    parse_front_matter,
    parse_knowledge_modules,
    validate_manifest,
)


def _minimal_doc(**overrides):
    meta = {
        'title': 'Test Doc',
        'category': 'sweden/test',
        'tags': ['unique-test-tag'],
        'country': 'SE',
        'language': 'en',
        'target_audience': 'editors',
        'difficulty': 'beginner',
        'last_updated': '2026-07-25',
        'references': [],
        'status': 'draft',
        'author': 'test',
        'version': '1.0',
    }
    meta.update(overrides)
    fm = yaml.safe_dump(meta, sort_keys=False)
    return f'---\n{fm}---\n\n# Body\n\nUseful content.\n'


class KnowledgeConfigFlagTests(unittest.TestCase):
    def test_all_knowledge_flags_disabled(self):
        self.assertFalse(ENABLE_KNOWLEDGE_ENGINE)
        self.assertFalse(ENABLE_RAG)
        self.assertFalse(ENABLE_KNOWLEDGE_INJECTION)


class ManifestAndParserTests(unittest.TestCase):
    def test_manifest_loading(self):
        raw = load_manifest(DEFAULT_KNOWLEDGE_ROOT / 'manifest.yaml')
        self.assertIn('modules', raw)
        self.assertIn('sweden__authorities__Skatteverket', raw['modules'])

    def test_parse_knowledge_modules(self):
        modules = parse_knowledge_modules()
        self.assertGreaterEqual(len(modules), 40)
        self.assertTrue(all(isinstance(m, KnowledgeModule) for m in modules))
        skatte = next(
            m for m in modules if m.file.endswith('Skatteverket.md')
        )
        self.assertEqual(skatte.metadata.get('category'), 'sweden/authorities')
        self.assertTrue(skatte.content.startswith('---'))

    def test_validate_manifest_success(self):
        raw = load_manifest(DEFAULT_KNOWLEDGE_ROOT / 'manifest.yaml')
        entries = validate_manifest(raw, DEFAULT_KNOWLEDGE_ROOT)
        self.assertEqual(len(entries), len(raw['modules']))

    def test_missing_manifest(self):
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(ManifestError):
                load_manifest(Path(tmp) / 'manifest.yaml')

    def test_missing_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'templates').mkdir()
            (root / 'templates' / 'guide.md').write_text(
                _minimal_doc(tags=['tpl-guide'], category='templates', title='T'),
                encoding='utf-8',
            )
            manifest = {
                'modules': {
                    'missing': {
                        'file': 'missing.md',
                        'title': 'Missing',
                        'tags': ['missing-tag'],
                        'priority': 1,
                    }
                }
            }
            with self.assertRaises(KnowledgeValidationError):
                validate_manifest(manifest, root)

    def test_duplicate_module_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'templates').mkdir()
            (root / 'templates' / 'guide.md').write_text(
                _minimal_doc(tags=['tpl-guide'], category='templates', title='T'),
                encoding='utf-8',
            )
            doc = root / 'a.md'
            doc.write_text(_minimal_doc(tags=['a-tag']), encoding='utf-8')
            manifest = {
                'modules': {
                    'one': {
                        'file': 'a.md',
                        'title': 'One',
                        'tags': ['one-tag'],
                        'priority': 1,
                    },
                    'two': {
                        'file': 'a.md',
                        'title': 'Two',
                        'tags': ['two-tag'],
                        'priority': 2,
                    },
                }
            }
            with self.assertRaises(KnowledgeValidationError) as ctx:
                validate_manifest(manifest, root)
            self.assertIn('Duplicate knowledge file', str(ctx.exception))

    def test_duplicate_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'templates').mkdir()
            (root / 'templates' / 'guide.md').write_text(
                _minimal_doc(tags=['tpl-guide'], category='templates', title='T'),
                encoding='utf-8',
            )
            (root / 'a.md').write_text(
                _minimal_doc(tags=['shared'], title='A', category='c/a'),
                encoding='utf-8',
            )
            (root / 'b.md').write_text(
                _minimal_doc(tags=['other'], title='B', category='c/b'),
                encoding='utf-8',
            )
            manifest = {
                'modules': {
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
            }
            with self.assertRaises(KnowledgeValidationError) as ctx:
                validate_manifest(manifest, root)
            self.assertIn('Duplicate tag', str(ctx.exception))

    def test_missing_metadata(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'templates').mkdir()
            (root / 'templates' / 'guide.md').write_text(
                _minimal_doc(tags=['tpl-guide'], category='templates', title='T'),
                encoding='utf-8',
            )
            (root / 'a.md').write_text('# No front matter\n', encoding='utf-8')
            manifest = {
                'modules': {
                    'a': {
                        'file': 'a.md',
                        'title': 'A',
                        'tags': ['a-tag'],
                        'priority': 1,
                    }
                }
            }
            with self.assertRaises(KnowledgeValidationError) as ctx:
                validate_manifest(manifest, root)
            self.assertIn('missing metadata', str(ctx.exception).lower())

    def test_empty_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / 'templates').mkdir()
            (root / 'templates' / 'guide.md').write_text(
                _minimal_doc(tags=['tpl-guide'], category='templates', title='T'),
                encoding='utf-8',
            )
            (root / 'a.md').write_text(
                _minimal_doc(tags=['a-tag']) + '\n',
                encoding='utf-8',
            )
            # overwrite body empty via front matter only
            (root / 'a.md').write_text(
                '---\n'
                + yaml.safe_dump(
                    {
                        'title': 'A',
                        'category': 'c',
                        'tags': ['a-tag'],
                        'country': 'SE',
                        'language': 'en',
                        'target_audience': 'editors',
                        'difficulty': 'beginner',
                        'last_updated': '2026-07-25',
                        'references': [],
                        'status': 'draft',
                        'author': 't',
                        'version': '1.0',
                    }
                )
                + '---\n\n   \n',
                encoding='utf-8',
            )
            manifest = {
                'modules': {
                    'a': {
                        'file': 'a.md',
                        'title': 'A',
                        'tags': ['a-tag'],
                        'priority': 1,
                    }
                }
            }
            with self.assertRaises(KnowledgeValidationError) as ctx:
                validate_manifest(manifest, root)
            self.assertIn('empty', str(ctx.exception).lower())


class SelectorInjectorFactoryTests(unittest.TestCase):
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
        self.assertIsInstance(get_knowledge_selector(), KeywordSelector)

    def test_factory_unknown(self):
        with self.assertRaises(ValueError):
            get_knowledge_selector('embedding')

    def test_injector_and_integration_noop(self):
        prompt = '## User Prompt\n\nHello\n'
        modules = parse_knowledge_modules()
        self.assertEqual(KnowledgeInjector().inject(prompt, modules), prompt)
        self.assertEqual(
            apply_knowledge_if_enabled(prompt, user_prompt='x'),
            prompt,
        )

    def test_prepare_knowledge_skipped_when_disabled(self):
        from content_ai.knowledge.integration import prepare_knowledge_for_context

        payload = prepare_knowledge_for_context(user_prompt='housing')
        self.assertEqual(payload.get('status'), 'skipped')

    def test_prepare_knowledge_when_engine_enabled(self):
        from content_ai.knowledge.integration import prepare_knowledge_for_context
        from unittest.mock import patch

        with patch(
            'content_ai.knowledge.integration.ENABLE_KNOWLEDGE_ENGINE',
            True,
        ):
            payload = prepare_knowledge_for_context(user_prompt='housing')
        self.assertEqual(payload.get('status'), 'prepared')
        self.assertGreater(payload.get('module_count', 0), 0)


class EditorialKnowledgeBaseLayoutTests(unittest.TestCase):
    def test_three_domains_exist(self):
        root = DEFAULT_KNOWLEDGE_ROOT
        for name in ('sweden', 'community', 'peyvand', 'templates'):
            self.assertTrue((root / name).is_dir(), msg=name)

    def test_style_guide_and_glossary_exist(self):
        root = DEFAULT_KNOWLEDGE_ROOT
        self.assertTrue(
            (root / 'peyvand/editorial_style/style_guide.md').is_file()
        )
        glossary = root / 'peyvand/terminology/glossary.md'
        self.assertTrue(glossary.is_file())
        terms = extract_glossary_terms(
            parse_front_matter(glossary.read_text(encoding='utf-8'))[1]
        )
        self.assertIn('personnummer', terms)
        self.assertIn('Skatteverket', terms)

    def test_authority_folder_populated(self):
        auth = DEFAULT_KNOWLEDGE_ROOT / 'sweden' / 'authorities'
        names = {p.name for p in auth.glob('*.md')}
        for required in (
            'Skatteverket.md',
            'Migrationsverket.md',
            'Försäkringskassan.md',
            'Arbetsförmedlingen.md',
            'CSN.md',
            'Kronofogden.md',
            'Polisen.md',
            'Kommun.md',
            'Region.md',
        ):
            self.assertIn(required, names)

    def test_templates_present(self):
        templates = {
            p.name
            for p in (DEFAULT_KNOWLEDGE_ROOT / 'templates').glob('*.md')
        }
        for required in (
            'authority.md',
            'concept.md',
            'guide.md',
            'process.md',
            'faq.md',
            'glossary_entry.md',
            'comparison.md',
            'editorial_policy.md',
            'knowledge_document.md',
        ):
            self.assertIn(required, templates)

    def test_prompt_builder_untouched_smoke(self):
        from content_ai.prompts.builders import PromptBuilder

        prompt = PromptBuilder().build(user_prompt='short request')
        self.assertIn('## User Prompt', prompt)
        self.assertNotIn('## Knowledge', prompt)


if __name__ == '__main__':
    unittest.main()
