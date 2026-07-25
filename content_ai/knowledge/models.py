"""Knowledge module data model (RFC-002)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class KnowledgeModule:
    """
    One editorial knowledge module loaded from the manifest + markdown.

    Future fields (language, country, version, last_updated) are intentionally
    omitted until a later RFC.
    """

    name: str
    title: str
    file: str
    tags: tuple[str, ...] = ()
    priority: int = 100
    content: str = ''
    metadata: dict = field(default_factory=dict)
