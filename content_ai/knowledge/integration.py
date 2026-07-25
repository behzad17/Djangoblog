"""Disabled integration helpers for a future PromptBuilder migration.

PromptBuilder is intentionally not modified. Callers may use
``apply_knowledge_if_enabled`` later; today every feature flag is False and
this function is a no-op.
"""

from __future__ import annotations

from content_ai.config.ai_engine import (
    ENABLE_KNOWLEDGE_ENGINE,
    ENABLE_KNOWLEDGE_INJECTION,
    ENABLE_RAG,
)
from content_ai.knowledge.injectors import KnowledgeInjector
from content_ai.knowledge.selectors import get_knowledge_selector
from content_ai.knowledge.utils import parse_knowledge_modules


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
