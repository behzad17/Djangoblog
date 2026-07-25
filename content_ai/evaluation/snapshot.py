"""Immutable evaluation snapshot for a single AI generation (RFC-004)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from content_ai.evaluation.exceptions import SnapshotError


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class EvaluationSnapshot:
    """
    Provider-independent record of one generation for evaluation.

    Immutable so comparisons and reports can treat snapshots as facts.
    """

    generation_id: str
    timestamp: datetime
    workflow_stage: str = ''
    prompt_version: str = ''
    knowledge_version: str = ''
    provider: str = ''
    model: str = ''
    language: str = ''
    input_text: str = ''
    output_text: str = ''
    input_size: int = 0
    output_size: int = 0
    token_usage: dict[str, Any] | None = None
    estimated_cost: float | None = None
    latency_ms: float | None = None
    warnings: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    scores: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def with_scores(self, scores: dict[str, float]) -> EvaluationSnapshot:
        """Return a copy with updated scores."""
        return EvaluationSnapshot(
            generation_id=self.generation_id,
            timestamp=self.timestamp,
            workflow_stage=self.workflow_stage,
            prompt_version=self.prompt_version,
            knowledge_version=self.knowledge_version,
            provider=self.provider,
            model=self.model,
            language=self.language,
            input_text=self.input_text,
            output_text=self.output_text,
            input_size=self.input_size,
            output_size=self.output_size,
            token_usage=self.token_usage,
            estimated_cost=self.estimated_cost,
            latency_ms=self.latency_ms,
            warnings=self.warnings,
            errors=self.errors,
            scores=dict(scores),
            metadata=dict(self.metadata),
        )


def create_snapshot(
    *,
    output_text: str = '',
    input_text: str = '',
    generation_id: str | None = None,
    workflow_stage: str = '',
    prompt_version: str = '',
    knowledge_version: str = '',
    provider: str = '',
    model: str = '',
    language: str = '',
    token_usage: dict[str, Any] | None = None,
    estimated_cost: float | None = None,
    latency_ms: float | None = None,
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> EvaluationSnapshot:
    """Build a validated EvaluationSnapshot."""
    gid = (generation_id or str(uuid4())).strip()
    if not gid:
        raise SnapshotError('generation_id must be a non-empty string.')
    out = output_text or ''
    inp = input_text or ''
    return EvaluationSnapshot(
        generation_id=gid,
        timestamp=utc_now(),
        workflow_stage=workflow_stage or '',
        prompt_version=prompt_version or '',
        knowledge_version=knowledge_version or '',
        provider=provider or '',
        model=model or '',
        language=language or '',
        input_text=inp,
        output_text=out,
        input_size=len(inp),
        output_size=len(out),
        token_usage=dict(token_usage) if token_usage else None,
        estimated_cost=estimated_cost,
        latency_ms=latency_ms,
        warnings=tuple(warnings or ()),
        errors=tuple(errors or ()),
        scores={},
        metadata=dict(metadata or {}),
    )


def validate_snapshot(snapshot: EvaluationSnapshot) -> None:
    """Validate required snapshot fields for evaluation."""
    if snapshot is None:
        raise SnapshotError('EvaluationSnapshot is required.')
    if not snapshot.generation_id:
        raise SnapshotError('Missing generation_id.')
    if snapshot.output_size < 0 or snapshot.input_size < 0:
        raise SnapshotError('input_size/output_size must be non-negative.')
    if snapshot.latency_ms is not None and snapshot.latency_ms < 0:
        raise SnapshotError('latency_ms must be non-negative.')
    if snapshot.estimated_cost is not None and snapshot.estimated_cost < 0:
        raise SnapshotError('estimated_cost must be non-negative.')
    for key, value in (snapshot.scores or {}).items():
        if not isinstance(value, (int, float)) or value < 0 or value > 1:
            raise SnapshotError(
                f'Score {key!r} must be a number in [0, 1], got {value!r}.'
            )
