"""Heuristic completeness metric."""

from __future__ import annotations

from content_ai.evaluation.metrics.base import EvaluationMetric
from content_ai.evaluation.scoring.score import MetricResult
from content_ai.evaluation.snapshot import EvaluationSnapshot


class CompletenessMetric(EvaluationMetric):
    name = 'completeness'
    default_weight = 1.2

    def evaluate(self, snapshot: EvaluationSnapshot) -> MetricResult:
        text = (snapshot.output_text or '').strip()
        size = len(text)
        if size == 0:
            score = 0.0
            explanation = 'Empty output.'
        elif size < 80:
            score = 0.35
            explanation = 'Very short output.'
        elif size < 250:
            score = 0.65
            explanation = 'Short but non-empty output.'
        else:
            score = 0.9
            explanation = 'Output length suggests a fuller draft.'
        return MetricResult(
            name=self.name,
            score=score,
            weight=self.default_weight,
            confidence=0.5,
            explanation=explanation,
        )
