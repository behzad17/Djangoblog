"""Keyword knowledge selector placeholder (no real retrieval yet)."""

from __future__ import annotations

from content_ai.knowledge.models import KnowledgeModule
from content_ai.knowledge.selectors.base import KnowledgeSelector


class KeywordSelector(KnowledgeSelector):
    """
    Placeholder keyword selector.

    Always returns an empty list. Real keyword matching is reserved for a
    future RFC.
    """

    def select(
        self,
        user_prompt: str,
        style: str = '',
        language: str = '',
        *,
        modules: list[KnowledgeModule] | None = None,
    ) -> list[KnowledgeModule]:
        return []
