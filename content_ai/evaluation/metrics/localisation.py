"""Heuristic Persian localisation metric."""

from __future__ import annotations

from content_ai.evaluation.metrics.base import EvaluationMetric
from content_ai.evaluation.scoring.score import MetricResult
from content_ai.evaluation.snapshot import EvaluationSnapshot


def _persian_ratio(text: str) -> float:
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return 0.0
    persian = sum(1 for c in letters if '\u0600' <= c <= '\u06FF')
    return persian / len(letters)


class LocalisationMetric(EvaluationMetric):
    name = 'localisation'
    default_weight = 1.3

    def evaluate(self, snapshot: EvaluationSnapshot) -> MetricResult:
        text = snapshot.output_text or ''
        if not text.strip():
            return MetricResult(
                name=self.name,
                score=0.0,
                weight=self.default_weight,
                confidence=1.0,
                warnings=('Empty output.',),
                explanation='No text for localisation scoring.',
            )
        ratio = _persian_ratio(text)
        lang = (snapshot.language or '').lower()
        if lang in ('fa', 'persian', 'farsi'):
            score = min(1.0, 0.3 + ratio * 0.7)
            explanation = (
                f'Language={lang}; Persian character ratio={ratio:.2f}.'
            )
        else:
            # Neutral when language is not Persian-targeted.
            score = 0.5 + min(ratio, 0.5) * 0.2
            explanation = (
                f'Language={lang or "unspecified"}; '
                f'Persian ratio={ratio:.2f} (informational).'
            )
        return MetricResult(
            name=self.name,
            score=round(score, 4),
            weight=self.default_weight,
            confidence=0.55,
            explanation=explanation,
        )
