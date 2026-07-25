"""Base metric interface for pluggable evaluation metrics."""

from __future__ import annotations

from abc import ABC, abstractmethod

from content_ai.evaluation.scoring.score import MetricResult
from content_ai.evaluation.snapshot import EvaluationSnapshot


class EvaluationMetric(ABC):
    """Pluggable metric. Implementations must be provider-independent."""

    name: str = ''
    default_weight: float = 1.0
    version: str = '1'

    @abstractmethod
    def evaluate(self, snapshot: EvaluationSnapshot) -> MetricResult:
        """Return a MetricResult for ``snapshot``."""
