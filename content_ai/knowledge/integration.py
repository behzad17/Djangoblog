"""Knowledge Engine integration helpers for production workflow (RFC-002).

PromptBuilder is intentionally not modified. Callers assemble prompts first,
then optionally inject knowledge via ``apply_knowledge_if_enabled``.
Preparation metadata is filled by ``prepare_knowledge_for_context``.
"""

from __future__ import annotations

from content_ai.config.ai_engine import (
    ENABLE_KNOWLEDGE_ENGINE,
    ENABLE_KNOWLEDGE_INJECTION,
    ENABLE_RAG,
)
from content_ai.knowledge.injectors import KnowledgeInjector
from content_ai.knowledge.selectors import get_knowledge_selector
from content_ai.knowledge.utils import (
    DEFAULT_KNOWLEDGE_ROOT,
    MANIFEST_FILENAME,
    load_manifest,
    parse_knowledge_modules,
)


def prepare_knowledge_for_context(
    *,
    user_prompt: str = '',
    style: str = '',
    language: str = '',
) -> dict:
    """
    Prepare knowledge metadata for workflow context.

    Soft-fails: returns a status payload and never raises.
    When ``ENABLE_KNOWLEDGE_ENGINE`` is False, returns ``status=skipped``.
    """
    if not ENABLE_KNOWLEDGE_ENGINE:
        return {
            'status': 'skipped',
            'module_count': 0,
            'selected_count': 0,
            'selected_names': [],
            'injection_enabled': False,
            'rag_enabled': False,
        }

    try:
        modules = parse_knowledge_modules()
        selected = []
        if ENABLE_RAG:
            selected = list(
                get_knowledge_selector().select(
                    user_prompt,
                    style=style,
                    language=language,
                    modules=modules,
                )
            )
        knowledge_version = ''
        try:
            manifest = load_manifest(
                DEFAULT_KNOWLEDGE_ROOT / MANIFEST_FILENAME
            )
            meta = manifest.get('_meta') or {}
            knowledge_version = str(meta.get('version') or '')
        except Exception:  # noqa: BLE001
            knowledge_version = ''

        return {
            'status': 'prepared',
            'module_count': len(modules),
            'selected_count': len(selected),
            'selected_names': [module.name for module in selected],
            'injection_enabled': bool(ENABLE_KNOWLEDGE_INJECTION),
            'rag_enabled': bool(ENABLE_RAG),
            'knowledge_version': knowledge_version,
        }
    except Exception as exc:  # noqa: BLE001 — soft-fail knowledge prep
        return {
            'status': 'failed_soft',
            'error': str(exc),
            'module_count': 0,
            'selected_count': 0,
            'selected_names': [],
            'injection_enabled': bool(ENABLE_KNOWLEDGE_INJECTION),
            'rag_enabled': bool(ENABLE_RAG),
        }


def apply_knowledge_if_enabled(
    prompt: str,
    *,
    user_prompt: str = '',
    style: str = '',
    language: str = '',
) -> str:
    """
    Optionally select and inject knowledge into ``prompt``.

    Returns ``prompt`` unchanged while Knowledge Engine / RAG / injection
    flags remain disabled.
    """
    if not (
        ENABLE_KNOWLEDGE_ENGINE
        and ENABLE_RAG
        and ENABLE_KNOWLEDGE_INJECTION
    ):
        return prompt

    modules = parse_knowledge_modules()
    selected = get_knowledge_selector().select(
        user_prompt,
        style=style,
        language=language,
        modules=modules,
    )
    return KnowledgeInjector().inject(prompt, selected)
