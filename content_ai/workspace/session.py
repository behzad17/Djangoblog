"""AI Editorial Workspace session models (APF-001)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from content_ai.editorial.content_types import (
    get_profile,
    resolve_content_type,
    resolve_goal,
)
from content_ai.workflow.states import WorkflowState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


PIPELINE_STEPS: tuple[tuple[str, str], ...] = (
    ('source_imported', 'Source imported'),
    ('metadata_extracted', 'Metadata extracted'),
    ('content_classified', 'Content classified'),
    ('goal_detected', 'Editorial goal detected'),
    ('draft_generated', 'Draft generated'),
    ('seo_ready', 'SEO ready'),
    ('fact_checked', 'Fact checked'),
    ('ready_for_publication', 'Ready for publication'),
)


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
    content_type: str = 'news'
    content_type_confidence: float = 0.0
    content_type_override: str = ''
    goal: str = 'inform'
    goal_confidence: float = 0.0
    goal_override: str = ''
    template_id: str = 'news.v1'
    pipeline: dict[str, bool] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def mark_pipeline(self, *step_ids: str) -> None:
        if not self.pipeline:
            self.pipeline = {key: False for key, _ in PIPELINE_STEPS}
        for step_id in step_ids:
            if step_id in dict(PIPELINE_STEPS):
                self.pipeline[step_id] = True

    def resolved_content_type(self) -> str:
        return resolve_content_type(
            self.content_type_override or self.content_type
        )

    def resolved_goal(self) -> str:
        return resolve_goal(
            self.goal_override or self.goal,
            content_type=self.resolved_content_type(),
        )

    def section_labels(self) -> dict[str, str]:
        return dict(get_profile(self.resolved_content_type()).section_labels)

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
        profile = get_profile(self.resolved_content_type())
        pipeline = {
            key: bool((self.pipeline or {}).get(key))
            for key, _ in PIPELINE_STEPS
        }
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
            'content_type': self.resolved_content_type(),
            'content_type_detected': self.content_type,
            'content_type_confidence': self.content_type_confidence,
            'content_type_override': self.content_type_override,
            'goal': self.resolved_goal(),
            'goal_detected': self.goal,
            'goal_confidence': self.goal_confidence,
            'goal_override': self.goal_override,
            'template_id': self.template_id or profile.resolved_template_id(),
            'lead_label': profile.lead_label,
            'section_labels': self.section_labels(),
            'pipeline': pipeline,
            'pipeline_steps': [
                {
                    'id': key,
                    'label': label,
                    'done': bool(pipeline.get(key)),
                }
                for key, label in PIPELINE_STEPS
            ],
            'updated_at': self.updated_at.isoformat(),
            'auto_publish_allowed': False,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> WorkspaceSession:
        data = data or {}
        state_raw = data.get('workflow_state') or WorkflowState.IDEA.value
        try:
            state = WorkflowState(state_raw)
        except ValueError:
            state = WorkflowState.IDEA
        session = cls(
            session_id=data.get('session_id') or str(uuid4()),
            workflow_state=state,
            language=data.get('language') or 'fa',
            audience=data.get('audience') or 'iranian-community-sweden',
            source_material=data.get('source_material') or '',
            source_url=data.get('source_url') or '',
            research_notes=data.get('research_notes') or '',
            sections=ArticleSections.from_dict(data.get('sections')),
            last_explanations=list(data.get('last_explanations') or []),
            metadata=dict(data.get('metadata') or {}),
            content_type=data.get('content_type_detected')
            or data.get('content_type')
            or 'news',
            content_type_confidence=float(
                data.get('content_type_confidence') or 0
            ),
            content_type_override=data.get('content_type_override') or '',
            goal=data.get('goal_detected') or data.get('goal') or 'inform',
            goal_confidence=float(data.get('goal_confidence') or 0),
            goal_override=data.get('goal_override') or '',
            template_id=data.get('template_id') or 'news.v1',
            pipeline=dict(data.get('pipeline') or {}),
        )
        history_raw = data.get('history') or []
        for item in history_raw:
            session.history.append(
                HistoryEntry(
                    entry_id=item.get('entry_id') or str(uuid4()),
                    label=item.get('label') or '',
                    sections=ArticleSections.from_dict(item.get('sections')),
                    explanation=item.get('explanation') or '',
                )
            )
        return session
