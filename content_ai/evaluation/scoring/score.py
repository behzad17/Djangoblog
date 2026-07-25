"""Metric and aggregate score models (RFC-004)."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class MetricResult:
    """Result returned by a single metric."""

    name: str
    score: float
    weight: float = 1.0
    confidence: float = 1.0
    warnings: tuple[str, ...] = ()
    explanation: str = ''

    def validate(self) -> None:
        from content_ai.evaluation.exceptions import MetricError

        if not self.name:
            raise MetricError('MetricResult.name is required.')
        for label, value in (
            ('score', self.score),
            ('weight', self.weight),
            ('confidence', self.confidence),
        ):
            if not isinstance(value, (int, float)):
                raise MetricError(f'{label} must be numeric.')
        if not 0 <= self.score <= 1:
            raise MetricError(
                f'score must be in [0, 1], got {self.score!r}.'
            )
        if self.weight < 0:
            raise MetricError(f'weight must be >= 0, got {self.weight!r}.')
        if not 0 <= self.confidence <= 1:
            raise MetricError(
                f'confidence must be in [0, 1], got {self.confidence!r}.'
            )


@dataclass(frozen=True, slots=True)
class AggregateScore:
    """Combined scores across metrics."""

    overall_score: float
    weighted_score: float
    normalised_score: float
    confidence_score: float
    metric_results: tuple[MetricResult, ...] = ()
    warnings: tuple[str, ...] = ()
    metadata: dict = field(default_factory=dict)
