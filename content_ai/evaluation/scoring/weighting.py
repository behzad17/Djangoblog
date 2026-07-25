"""Aggregate metric results into overall scores."""

from __future__ import annotations

from content_ai.evaluation.exceptions import MetricError
from content_ai.evaluation.scoring.score import AggregateScore, MetricResult


def aggregate_scores(
    results: list[MetricResult] | tuple[MetricResult, ...],
) -> AggregateScore:
    """
    Calculate overall, weighted, normalised, and confidence scores.

    Scores are expected in [0, 1]. Weights must be non-negative.
    """
    items = list(results or [])
    if not items:
        raise MetricError('Cannot aggregate an empty metric result list.')

    warnings: list[str] = []
    for item in items:
        item.validate()
        warnings.extend(item.warnings)

    total_weight = sum(item.weight for item in items)
    if total_weight <= 0:
        raise MetricError('Total metric weight must be > 0.')

    weighted = sum(item.score * item.weight for item in items) / total_weight
    simple = sum(item.score for item in items) / len(items)
    # Normalised: weighted score already in [0,1]; keep alias for API clarity.
    normalised = max(0.0, min(1.0, weighted))
    confidence = sum(
        item.confidence * item.weight for item in items
    ) / total_weight

    return AggregateScore(
        overall_score=round(simple, 6),
        weighted_score=round(weighted, 6),
        normalised_score=round(normalised, 6),
        confidence_score=round(confidence, 6),
        metric_results=tuple(items),
        warnings=tuple(warnings),
    )
