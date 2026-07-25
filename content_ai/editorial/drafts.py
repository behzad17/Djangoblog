"""In-memory editorial draft objects. No Django models or persistence."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class EditorialDraft:
    """
    Lightweight editorial draft produced by Content AI.

    Not a Blog Post. Not saved to the database.
    """

    title: str = ''
    body: str = ''
    summary: str = ''
    language: str = ''
    metadata: dict = field(default_factory=dict)
