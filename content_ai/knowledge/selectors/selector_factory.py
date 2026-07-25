"""Factory for knowledge selectors (architecture placeholder)."""

from __future__ import annotations

from content_ai.knowledge.selectors.base import KnowledgeSelector
from content_ai.knowledge.selectors.keyword_selector import KeywordSelector

# Future: 'embedding' | 'hybrid' | 'semantic'
DEFAULT_SELECTOR_NAME = 'keyword'


def get_knowledge_selector(name: str | None = None) -> KnowledgeSelector:
    """
    Return a knowledge selector instance.

    Only ``keyword`` is implemented (placeholder, returns no modules).
    """
    selector_name = (name or DEFAULT_SELECTOR_NAME).strip().lower()
    if selector_name == 'keyword':
        return KeywordSelector()
    raise ValueError(
        f"Unknown knowledge selector {selector_name!r}. "
        f"Supported: {DEFAULT_SELECTOR_NAME!r}."
    )
