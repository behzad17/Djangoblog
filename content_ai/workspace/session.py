"""AI Editorial Workspace session models (APF-001)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from content_ai.workflow.states import WorkflowState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ArticleSections:
    """Independently editable generated sections."""

    headline: str = ''
    lead: str = ''
    body: str = ''
    summary: str = ''
    category: str = ''
    tags: list[str] = field(default_factory=list)
    excerpt: str = ''

    def to_dict(self) -> dict[str, Any]:
        return {
            'headline': self.headline,
            'lead': self.lead,
            'body': self.body,
            'summary': self.summary,
            'category': self.category,
            'tags': list(self.tags),
            'excerpt': self.excerpt,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> ArticleSections:
        data = data or {}
        return cls(
            headline=data.get('headline') or '',
            lead=data.get('lead') or '',
            body=data.get('body') or '',
            summary=data.get('summary') or '',
            category=data.get('category') or '',
            tags=list(data.get('tags') or []),
            excerpt=data.get('excerpt') or '',
        )


@dataclass
class HistoryEntry:
    entry_id: str
    label: str
    sections: ArticleSections
    explanation: str = ''
    created_at: datetime = field(default_factory=utc_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            'entry_id': self.entry_id,
            'label': self.label,
            'sections': self.sections.to_dict(),
            'explanation': self.explanation,
            'created_at': self.created_at.isoformat(),
        }


@dataclass
class WorkspaceSession:
    """
    In-memory editorial workspace session (not persisted by default).

    Composes workflow state, sections, sources, and local history.
    """

    session_id: str = field(default_factory=lambda: str(uuid4()))
    workflow_state: WorkflowState = WorkflowState.IDEA
    language: str = 'fa'
    audience: str = 'iranian-community-sweden'
    source_material: str = ''
    source_url: str = ''
    research_notes: str = ''
    sections: ArticleSections = field(default_factory=ArticleSections)
    history: list[HistoryEntry] = field(default_factory=list)
    last_explanations: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def push_history(self, label: str, explanation: str = '') -> HistoryEntry:
        entry = HistoryEntry(
            entry_id=str(uuid4()),
            label=label,
            sections=ArticleSections.from_dict(self.sections.to_dict()),
            explanation=explanation,
        )
        self.history.append(entry)
        # Keep a bounded local ring (architecture; not durable storage).
        if len(self.history) > 20:
            self.history = self.history[-20:]
        self.touch()
        return entry

    def restore_history(self, entry_id: str) -> bool:
        for entry in self.history:
            if entry.entry_id == entry_id:
                self.sections = ArticleSections.from_dict(entry.sections.to_dict())
                self.last_explanations = [
                    f'Restored revision: {entry.label}',
                    entry.explanation,
                ]
                self.touch()
                return True
        return False

    def to_dict(self) -> dict[str, Any]:
        return {
            'session_id': self.session_id,
            'workflow_state': self.workflow_state.value,
            'language': self.language,
            'audience': self.audience,
            'source_material': self.source_material,
            'source_url': self.source_url,
            'research_notes': self.research_notes,
            'sections': self.sections.to_dict(),
            'history': [item.to_dict() for item in self.history],
            'last_explanations': list(self.last_explanations),
            'metadata': dict(self.metadata),
            'updated_at': self.updated_at.isoformat(),
            'auto_publish_allowed': False,
        }
