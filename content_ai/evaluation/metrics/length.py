"""Heuristic output-length metric."""

from __future__ import annotations

from content_ai.evaluation.metrics.base import EvaluationMetric
from content_ai.evaluation.scoring.score import MetricResult
from content_ai.evaluation.snapshot import EvaluationSnapshot


class OutputLengthMetric(EvaluationMetric):
    name = 'output_length'
    default_weight = 0.6

    def evaluate(self, snapshot: EvaluationSnapshot) -> MetricResult:
        size = snapshot.output_size or len(snapshot.output_text or '')
        if size <= 0:
            score = 0.0
            explanation = 'Empty output.'
        elif size < 100:
            score = 0.4
            explanation = f'Output length={size} (short).'
        elif size <= 4000:
            score = 0.85
            explanation = f'Output length={size} (within typical band).'
        else:
            score = 0.6
            explanation = f'Output length={size} (very long).'
        return MetricResult(
            name=self.name,
            score=score,
            weight=self.default_weight,
            confidence=0.7,
            explanation=explanation,
        )
