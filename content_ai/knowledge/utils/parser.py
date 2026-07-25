"""Load and validate knowledge manifest + markdown modules."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from content_ai.knowledge.exceptions import (
    KnowledgeValidationError,
    ManifestError,
)
from content_ai.knowledge.models import KnowledgeModule

DEFAULT_KNOWLEDGE_ROOT = Path(__file__).resolve().parents[1]
MANIFEST_FILENAME = 'manifest.yaml'


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


def _normalize_tags(tags: Any, module_name: str) -> tuple[str, ...]:
    if tags is None:
        return ()
    if not isinstance(tags, list):
        raise KnowledgeValidationError(
            f"Module {module_name!r}: 'tags' must be a list."
        )
    normalized: list[str] = []
    for tag in tags:
        if not isinstance(tag, str) or not tag.strip():
            raise KnowledgeValidationError(
                f"Module {module_name!r}: tags must be non-empty strings."
            )
        normalized.append(tag.strip())
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
    }


def validate_manifest(
    raw: dict[str, Any],
    knowledge_root: Path,
) -> list[dict[str, Any]]:
    """
    Validate manifest integrity.

    Checks: metadata shape, missing markdown files, duplicate module names
    (implicit via mapping), and duplicate tags across modules.
    """
    if not raw:
        raise KnowledgeValidationError('Knowledge manifest is empty.')

    entries: list[dict[str, Any]] = []
    seen_tags: dict[str, str] = {}
    for name, entry in raw.items():
        normalized = _validate_entry(name, entry)
        md_path = knowledge_root / normalized['file']
        if not md_path.is_file():
            raise KnowledgeValidationError(
                f"Module {normalized['name']!r}: markdown file missing "
                f"({md_path})."
            )
        for tag in normalized['tags']:
            key = tag.casefold()
            if key in seen_tags:
                raise KnowledgeValidationError(
                    f"Duplicate tag {tag!r} in modules "
                    f"{seen_tags[key]!r} and {normalized['name']!r}."
                )
            seen_tags[key] = normalized['name']
        entries.append(normalized)
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
            )
        )
    return modules
