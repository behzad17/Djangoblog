"""Heuristic terminology consistency metric."""

from __future__ import annotations

from collections import Counter

from content_ai.evaluation.metrics.base import EvaluationMetric
from content_ai.evaluation.scoring.score import MetricResult
from content_ai.evaluation.snapshot import EvaluationSnapshot


class ConsistencyMetric(EvaluationMetric):
    name = 'consistency'
    default_weight = 1.0

    def evaluate(self, snapshot: EvaluationSnapshot) -> MetricResult:
        text = (snapshot.output_text or '').lower()
        if not text.strip():
            return MetricResult(
                name=self.name,
                score=0.0,
                weight=self.default_weight,
                confidence=1.0,
                warnings=('Empty output.',),
                explanation='No text for consistency scoring.',
            )
        tokens = [t.strip('.,;:()[]\"\'') for t in text.split() if len(t) > 3]
        if len(tokens) < 10:
            return MetricResult(
                name=self.name,
                score=0.6,
                weight=self.default_weight,
                confidence=0.4,
                explanation='Too little text for strong consistency signal.',
            )
        counts = Counter(tokens)
        repeated = sum(1 for _, c in counts.items() if c >= 2)
        ratio = repeated / max(len(counts), 1)
        score = max(0.35, min(0.95, 0.45 + ratio))
        return MetricResult(
            name=self.name,
            score=round(score, 4),
            weight=self.default_weight,
            confidence=0.45,
            explanation=f'Repeated-term ratio={ratio:.2f}.',
        )
