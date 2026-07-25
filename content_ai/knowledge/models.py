"""Knowledge module data model (RFC-002 / RFC-002.5)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class KnowledgeModule:
    """
    One editorial knowledge document loaded from the manifest + markdown.

    Editorial metadata (category, country, language, …) lives in ``metadata``
    and is validated from YAML front matter when present.
    """

    name: str
    title: str
    file: str
    tags: tuple[str, ...] = ()
    priority: int = 100
    content: str = ''
    metadata: dict = field(default_factory=dict)
