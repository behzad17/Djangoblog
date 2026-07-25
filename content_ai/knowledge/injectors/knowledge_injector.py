"""Inject selected knowledge into prompts (inactive / no-op for now)."""

from __future__ import annotations

from content_ai.knowledge.models import KnowledgeModule


class KnowledgeInjector:
    """
    Merge knowledge modules into a prompt string.

    Current behaviour: return the prompt unchanged. Real injection is gated
    behind ``ENABLE_KNOWLEDGE_INJECTION`` in a future migration.
    """

    def inject(
        self,
        prompt: str,
        modules: list[KnowledgeModule] | None = None,
    ) -> str:
        """Return ``prompt`` unchanged (no knowledge injection yet)."""
        return prompt
