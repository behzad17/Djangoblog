"""Heuristic readability metric (architecture placeholder)."""

from __future__ import annotations

from content_ai.evaluation.metrics.base import EvaluationMetric
from content_ai.evaluation.scoring.score import MetricResult
from content_ai.evaluation.snapshot import EvaluationSnapshot


class ReadabilityMetric(EvaluationMetric):
    name = 'readability'
    default_weight = 1.0

    def evaluate(self, snapshot: EvaluationSnapshot) -> MetricResult:
        text = (snapshot.output_text or '').strip()
        if not text:
            return MetricResult(
                name=self.name,
                score=0.0,
                weight=self.default_weight,
                confidence=1.0,
                warnings=('Empty output.',),
                explanation='No text to score for readability.',
            )
        words = text.split()
        sentences = max(text.count('.') + text.count('!') + text.count('؟'), 1)
        avg_words = len(words) / sentences
        # Prefer moderate sentence length (~12–22 words).
        if 12 <= avg_words <= 22:
            score = 0.9
        elif 8 <= avg_words < 12 or 22 < avg_words <= 30:
            score = 0.7
        elif avg_words < 8:
            score = 0.55
        else:
            score = 0.4
        return MetricResult(
            name=self.name,
            score=score,
            weight=self.default_weight,
            confidence=0.6,
            explanation=f'Average words/sentence ≈ {avg_words:.1f}.',
        )
