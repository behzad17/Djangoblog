"""Abstract knowledge selector interface."""

from __future__ import annotations

from abc import ABC, abstractmethod

from content_ai.knowledge.models import KnowledgeModule


class KnowledgeSelector(ABC):
    """
    Select relevant knowledge modules for a user prompt.

    Implementations must remain inactive in production until RAG is enabled.
    """

    @abstractmethod
    def select(
        self,
        user_prompt: str,
        style: str = '',
        language: str = '',
        *,
        modules: list[KnowledgeModule] | None = None,
    ) -> list[KnowledgeModule]:
        """Return knowledge modules relevant to the request (may be empty)."""
