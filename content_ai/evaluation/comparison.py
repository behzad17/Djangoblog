"""Compare evaluation snapshots across dimensions (RFC-004)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from content_ai.evaluation.exceptions import ComparisonError
from content_ai.evaluation.snapshot import EvaluationSnapshot, validate_snapshot


@dataclass(frozen=True, slots=True)
class ComparisonResult:
    dimension: str
    groups: dict[str, list[str]] = field(default_factory=dict)
    averages: dict[str, float] = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)


_DIMENSIONS = frozenset({
    'prompt_version',
    'knowledge_version',
    'provider',
    'model',
    'workflow_stage',
    'language',
    'generation_date',
})


class ComparisonEngine:
    """
    Group snapshots by a dimension and average overall-like scores.

    Does not assume OpenAI. Future dimensions (temperature, agents, …)
    can be added without changing callers.
    """

    def compare(
        self,
        snapshots: Iterable[EvaluationSnapshot],
        *,
        dimension: str,
        score_key: str = 'overall',
    ) -> ComparisonResult:
        if dimension not in _DIMENSIONS:
            raise ComparisonError(
                f'Unknown comparison dimension: {dimension!r}. '
                f'Supported: {", ".join(sorted(_DIMENSIONS))}.'
            )
        items = list(snapshots or [])
        if not items:
            raise ComparisonError('No snapshots to compare.')

        groups: dict[str, list[str]] = {}
        totals: dict[str, list[float]] = {}

        for snap in items:
            validate_snapshot(snap)
            key = self._dimension_value(snap, dimension)
            groups.setdefault(key, []).append(snap.generation_id)
            score = self._score(snap, score_key)
            totals.setdefault(key, []).append(score)

        averages = {
            key: round(sum(vals) / len(vals), 6)
            for key, vals in totals.items()
        }
        return ComparisonResult(
            dimension=dimension,
            groups=groups,
            averages=averages,
            metadata={'score_key': score_key, 'count': len(items)},
        )

    def _dimension_value(
        self,
        snapshot: EvaluationSnapshot,
        dimension: str,
    ) -> str:
        if dimension == 'generation_date':
            return snapshot.timestamp.date().isoformat()
        value = getattr(snapshot, dimension, '') or 'unknown'
        return str(value)

    def _score(self, snapshot: EvaluationSnapshot, score_key: str) -> float:
        if score_key == 'overall':
            scores = list((snapshot.scores or {}).values())
            if not scores:
                return 0.0
            return sum(scores) / len(scores)
        if score_key not in (snapshot.scores or {}):
            raise ComparisonError(
                f'Score key {score_key!r} missing on snapshot '
                f'{snapshot.generation_id!r}.'
            )
        return float(snapshot.scores[score_key])
