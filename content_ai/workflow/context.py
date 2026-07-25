"""Shared workflow context passed between stages (RFC-003)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from content_ai.workflow.exceptions import ContextError
from content_ai.workflow.states import WorkflowState


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class StageLogEntry:
    """Provider-independent record for one stage execution."""

    stage_name: str
    status: str
    started_at: datetime | None = None
    finished_at: datetime | None = None
    duration_ms: float | None = None
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    prompt_version: str = ''
    knowledge_version: str = ''
    provider: str = ''
    model: str = ''
    token_usage: dict[str, Any] | None = None
    estimated_cost: float | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowContext:
    """
    Shared mutable context for the editorial workflow.

    Stages receive and update this object. Stages must not call each other.
    Future RFCs should extend fields rather than replace this type.
    """

    state: WorkflowState = WorkflowState.IDEA
    article_metadata: dict[str, Any] = field(default_factory=dict)
    language: str = ''
    audience: str = ''
    prompt_version: str = ''
    knowledge_version: str = ''
    input_sources: list[str] = field(default_factory=list)
    generated_draft: str = ''
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    editorial_notes: list[str] = field(default_factory=list)
    token_usage: dict[str, Any] | None = None
    estimated_cost: float | None = None
    execution_time_ms: float | None = None
    provider: str = ''
    model: str = ''
    stage_logs: list[StageLogEntry] = field(default_factory=list)
    extension_data: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=utc_now)
    updated_at: datetime = field(default_factory=utc_now)

    def touch(self) -> None:
        self.updated_at = utc_now()

    def add_warning(self, message: str) -> None:
        self.warnings.append(message)
        self.touch()

    def add_error(self, message: str) -> None:
        self.errors.append(message)
        self.touch()

    def add_note(self, message: str) -> None:
        self.editorial_notes.append(message)
        self.touch()

    def record_stage(self, entry: StageLogEntry) -> None:
        self.stage_logs.append(entry)
        self.touch()

    def require_article_metadata(self, *keys: str) -> None:
        missing = [k for k in keys if not self.article_metadata.get(k)]
        if missing:
            raise ContextError(
                'WorkflowContext missing article metadata: '
                + ', '.join(missing)
            )

    def validate_present(self) -> None:
        if self is None:  # pragma: no cover - defensive
            raise ContextError('WorkflowContext is required.')
        if not isinstance(self.state, WorkflowState):
            raise ContextError('WorkflowContext.state must be a WorkflowState.')
