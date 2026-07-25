"""High-level evaluator that runs metrics against a snapshot."""

from __future__ import annotations

from dataclasses import dataclass

from content_ai.evaluation.exceptions import EvaluationError
from content_ai.evaluation.registry import MetricRegistry, build_default_registry
from content_ai.evaluation.scoring.score import AggregateScore
from content_ai.evaluation.scoring.weighting import aggregate_scores
from content_ai.evaluation.snapshot import (
    EvaluationSnapshot,
    validate_snapshot,
)


@dataclass(frozen=True, slots=True)
class EvaluationResult:
    snapshot: EvaluationSnapshot
    aggregate: AggregateScore


class Evaluator:
    """
    Evaluate AI output via the metric registry.

    Passive: does not call providers, prompt engine, workflow, or knowledge.
    """

    def __init__(self, registry: MetricRegistry | None = None):
        self.registry = registry or build_default_registry()

    def evaluate(
        self,
        snapshot: EvaluationSnapshot,
        metric_names: list[str] | None = None,
    ) -> EvaluationResult:
        if snapshot is None:
            raise EvaluationError('snapshot is required.')
        validate_snapshot(snapshot)
        results = self.registry.execute(snapshot, names=metric_names)
        aggregate = aggregate_scores(results)
        scored = snapshot.with_scores(
            {item.name: item.score for item in results}
        )
        return EvaluationResult(snapshot=scored, aggregate=aggregate)
