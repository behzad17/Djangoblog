"""Heuristic structure metric."""

from __future__ import annotations

from content_ai.evaluation.metrics.base import EvaluationMetric
from content_ai.evaluation.scoring.score import MetricResult
from content_ai.evaluation.snapshot import EvaluationSnapshot


class StructureMetric(EvaluationMetric):
    name = 'structure'
    default_weight = 1.0

    def evaluate(self, snapshot: EvaluationSnapshot) -> MetricResult:
        text = snapshot.output_text or ''
        if not text.strip():
            return MetricResult(
                name=self.name,
                score=0.0,
                weight=self.default_weight,
                confidence=1.0,
                warnings=('Empty output.',),
                explanation='No structure detectable.',
            )
        paragraphs = [p for p in text.split('\n\n') if p.strip()]
        headings = sum(
            1 for line in text.splitlines() if line.strip().startswith('#')
        )
        score = 0.4
        if len(paragraphs) >= 2:
            score += 0.3
        if headings >= 1:
            score += 0.2
        if len(text) >= 200:
            score += 0.1
        score = min(score, 1.0)
        return MetricResult(
            name=self.name,
            score=round(score, 4),
            weight=self.default_weight,
            confidence=0.55,
            explanation=(
                f'paragraphs={len(paragraphs)} headings={headings}.'
            ),
        )
