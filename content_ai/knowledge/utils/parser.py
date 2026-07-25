"""Load and validate knowledge manifest + markdown modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any
import re

import yaml

from content_ai.knowledge.exceptions import (
    KnowledgeValidationError,
    ManifestError,
)
from content_ai.knowledge.models import KnowledgeModule

DEFAULT_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_FILENAME = 'manifest.yaml'

REQUIRED_FRONT_MATTER_FIELDS: tuple[str, ...] = (
    'title',
    'category',
    'tags',
    'country',
    'language',
    'target_audience',
    'difficulty',
    'last_updated',
    'references',
    'status',
    'author',
    'version',
)

GLOSSARY_TERM_RE = re.compile(
    r'^##\s+(?P<term>.+?)\s*$',
    re.MULTILINE,
)


def load_manifest(path: Path) -> dict[str, Any]:
    """Load and return the raw manifest mapping."""
    if not path.is_file():
        raise ManifestError(f'Knowledge manifest not found: {path}.')
    try:
        raw = yaml.safe_load(path.read_text(encoding='utf-8'))
    except yaml.YAMLError as exc:
        raise ManifestError(f'Invalid knowledge manifest YAML: {exc}') from exc
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ManifestError(
            'Knowledge manifest must be a mapping of module name → metadata.'
        )
    return raw


def manifest_modules(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Return the module mapping from a manifest.

    Supports RFC-002 flat maps and RFC-002.5 ``modules:`` nesting.
    """
    if 'modules' in raw:
        modules = raw.get('modules')
        if modules is None:
            return {}
        if not isinstance(modules, dict):
            raise ManifestError("Manifest key 'modules' must be a mapping.")
        return modules
    # Flat legacy: ignore underscore meta keys if any.
    return {k: v for k, v in raw.items() if not str(k).startswith('_')}


def parse_front_matter(text: str) -> tuple[dict[str, Any], str]:
    """Split YAML front matter from markdown body."""
    if not text.startswith('---'):
        return {}, text
    end = text.find('\n---', 3)
    if end < 0:
        raise KnowledgeValidationError('Unterminated YAML front matter.')
    fm_raw = text[3:end]
    body = text[end + 4:].lstrip('\n')
    try:
        data = yaml.safe_load(fm_raw) or {}
    except yaml.YAMLError as exc:
        raise KnowledgeValidationError(
            f'Invalid YAML front matter: {exc}'
        ) from exc
    if not isinstance(data, dict):
        raise KnowledgeValidationError('Front matter must be a mapping.')
    return data, body


def _normalize_tags(tags: Any, module_name: str) -> tuple[str, ...]:
    if tags is None:
        return ()
    if not isinstance(tags, list):
        raise KnowledgeValidationError(
            f"Module {module_name!r}: 'tags' must be a list."
        )
    normalized: list[str] = []
    seen: set[str] = set()
    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            raise KnowledgeValidationError(
                f"Module {module_name!r}: tags must be non-empty strings."
            )
        value = tag.strip()
        key = value.casefold()
        if key in seen:
            raise KnowledgeValidationError(
                f"Module {module_name!r}: duplicate tag {value!r}."
            )
        seen.add(key)
        normalized.append(value)
    return tuple(normalized)


def _validate_entry(name: str, entry: Any) -> dict[str, Any]:
    if not isinstance(name, str) or not name.strip():
        raise KnowledgeValidationError('Module name must be a non-empty string.')
    if not isinstance(entry, dict):
        raise KnowledgeValidationError(
            f"Module {name!r}: metadata must be a mapping."
        )
    file_name = entry.get('file')
    if not isinstance(file_name, str) or not file_name.strip():
        raise KnowledgeValidationError(
            f"Module {name!r}: missing or invalid 'file'."
        )
    # Reject path traversal outside knowledge root.
    if Path(file_name).is_absolute() or '..' in Path(file_name).parts:
        raise KnowledgeValidationError(
            f"Module {name!r}: invalid file path {file_name!r}."
        )
    title = entry.get('title', name)
    if not isinstance(title, str) or not title.strip():
        raise KnowledgeValidationError(
            f"Module {name!r}: 'title' must be a non-empty string."
        )
    priority = entry.get('priority', 100)
    if not isinstance(priority, int) or isinstance(priority, bool):
        raise KnowledgeValidationError(
            f"Module {name!r}: 'priority' must be an integer."
        )
    tags = _normalize_tags(entry.get('tags'), name)
    return {
        'name': name.strip(),
        'title': title.strip(),
        'file': file_name.strip(),
        'tags': tags,
        'priority': priority,
        'category': entry.get('category', ''),
        'domain': entry.get('domain', ''),
    }


def validate_front_matter(
    module_name: str,
    front_matter: dict[str, Any],
) -> None:
    """Ensure required editorial metadata fields are present and typed."""
    missing = [
        field
        for field in REQUIRED_FRONT_MATTER_FIELDS
        if field not in front_matter
    ]
    if missing:
        raise KnowledgeValidationError(
            f"Module {module_name!r}: missing metadata fields: "
            + ', '.join(missing)
        )
    title = front_matter.get('title')
    if not isinstance(title, str) or not title.strip():
        raise KnowledgeValidationError(
            f"Module {module_name!r}: metadata title must be a non-empty string."
        )
    category = front_matter.get('category')
    if not isinstance(category, str) or not category.strip():
        raise KnowledgeValidationError(
            f"Module {module_name!r}: metadata category must be a non-empty string."
        )
    _normalize_tags(front_matter.get('tags'), module_name)
    refs = front_matter.get('references')
    if refs is None:
        raise KnowledgeValidationError(
            f"Module {module_name!r}: references must be a list (may be empty)."
        )
    if not isinstance(refs, list):
        raise KnowledgeValidationError(
            f"Module {module_name!r}: references must be a list."
        )


def validate_not_empty(module_name: str, body: str, path: Path) -> None:
    if not (body or '').strip():
        raise KnowledgeValidationError(
            f"Module {module_name!r}: empty knowledge file ({path})."
        )


def validate_references(
    module_name: str,
    references: list[Any],
    knowledge_root: Path,
) -> None:
    """Validate relative markdown references exist when they look like paths."""
    for ref in references:
        if not isinstance(ref, str):
            raise KnowledgeValidationError(
                f"Module {module_name!r}: references must be strings."
            )
        value = ref.strip()
        if not value:
            continue
        if value.endswith('.md') and ('/' in value or value.endswith('.md')):
            # Treat as repo-relative knowledge path when it points under known roots.
            candidate = knowledge_root / value
            if value.startswith(('sweden/', 'community/', 'peyvand/', 'templates/')):
                if not candidate.is_file():
                    raise KnowledgeValidationError(
                        f"Module {module_name!r}: broken reference {value!r}."
                    )


def extract_glossary_terms(content: str) -> list[str]:
    """Extract glossary Swedish term headings (``## term``)."""
    return [m.group('term').strip() for m in GLOSSARY_TERM_RE.finditer(content)]


def validate_glossary_terms(content: str, module_name: str) -> None:
    terms = extract_glossary_terms(content)
    seen: dict[str, str] = {}
    for term in terms:
        key = term.casefold()
        if key in seen:
            raise KnowledgeValidationError(
                f"Module {module_name!r}: duplicate glossary term {term!r}."
            )
        seen[key] = term


def validate_templates(knowledge_root: Path) -> None:
    templates_dir = knowledge_root / 'templates'
    if not templates_dir.is_dir():
        raise KnowledgeValidationError(
            f'Templates directory missing: {templates_dir}.'
        )
    names: dict[str, Path] = {}
    for path in templates_dir.glob('*.md'):
        key = path.name.casefold()
        if key in names:
            raise KnowledgeValidationError(
                f'Duplicate template file name: {path.name}.'
            )
        names[key] = path
        text = path.read_text(encoding='utf-8')
        if not text.strip():
            raise KnowledgeValidationError(f'Empty template file: {path}.')


def validate_manifest(
    raw: dict[str, Any],
    knowledge_root: Path,
) -> list[dict[str, Any]]:
    """
    Validate manifest integrity and linked markdown documents.

    Checks: metadata shape, missing files, empty files, front matter,
    duplicate module file paths, duplicate tags across modules, duplicate
    categories used by multiple modules with the same title, templates,
    glossary term uniqueness, and relative references.
    """
    modules_raw = manifest_modules(raw)
    if not modules_raw:
        raise KnowledgeValidationError('Knowledge manifest has no modules.')

    entries: list[dict[str, Any]] = []
    seen_tags: dict[str, str] = {}
    seen_files: dict[str, str] = {}
    seen_categories: dict[str, str] = {}
    seen_names: set[str] = set()

    for name, entry in modules_raw.items():
        if name in seen_names:
            raise KnowledgeValidationError(
                f'Duplicate module name {name!r}.'
            )
        seen_names.add(name)
        normalized = _validate_entry(name, entry)
        file_key = normalized['file'].casefold()
        if file_key in seen_files:
            raise KnowledgeValidationError(
                f"Duplicate knowledge file {normalized['file']!r} for modules "
                f"{seen_files[file_key]!r} and {normalized['name']!r}."
            )
        seen_files[file_key] = normalized['name']

        md_path = knowledge_root / normalized['file']
        if not md_path.is_file():
            raise KnowledgeValidationError(
                f"Module {normalized['name']!r}: markdown file missing "
                f"({md_path})."
            )
        text = md_path.read_text(encoding='utf-8')
        front_matter, body = parse_front_matter(text)
        validate_front_matter(normalized['name'], front_matter)
        validate_not_empty(normalized['name'], body, md_path)
        validate_references(
            normalized['name'],
            front_matter.get('references') or [],
            knowledge_root,
        )

        category = str(front_matter.get('category', '')).strip()
        # Duplicate category means two modules claim the same category AND title.
        cat_key = f"{category.casefold()}::{str(front_matter.get('title', '')).casefold()}"
        if cat_key in seen_categories:
            raise KnowledgeValidationError(
                f"Duplicate knowledge document category/title "
                f"{category!r}/{front_matter.get('title')!r} for modules "
                f"{seen_categories[cat_key]!r} and {normalized['name']!r}."
            )
        seen_categories[cat_key] = normalized['name']

        for tag in normalized['tags']:
            key = tag.casefold()
            if key in seen_tags:
                raise KnowledgeValidationError(
                    f"Duplicate tag {tag!r} in modules "
                    f"{seen_tags[key]!r} and {normalized['name']!r}."
                )
            seen_tags[key] = normalized['name']

        if 'glossary' in normalized['file'].casefold():
            validate_glossary_terms(body, normalized['name'])

        normalized['front_matter'] = front_matter
        normalized['body'] = body
        entries.append(normalized)

    validate_templates(knowledge_root)
    return entries


def parse_knowledge_modules(
    knowledge_root: Path | None = None,
    *,
    load_content: bool = True,
) -> list[KnowledgeModule]:
    """
    Load manifest, validate metadata, and return KnowledgeModule objects.

    Does not perform retrieval or injection.
    """
    root = knowledge_root or DEFAULT_KNOWLEDGE_ROOT
    manifest_path = root / MANIFEST_FILENAME
    raw = load_manifest(manifest_path)
    entries = validate_manifest(raw, root)
    modules: list[KnowledgeModule] = []
    for entry in entries:
        content = ''
        if load_content:
            content = (root / entry['file']).read_text(encoding='utf-8')
        modules.append(
            KnowledgeModule(
                name=entry['name'],
                title=entry['title'],
                file=entry['file'],
                tags=entry['tags'],
                priority=entry['priority'],
                content=content,
                metadata=dict(entry.get('front_matter') or {}),
            )
        )
    return modules
