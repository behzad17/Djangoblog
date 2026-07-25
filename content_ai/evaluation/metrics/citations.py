"""Heuristic citation presence metric."""

from __future__ import annotations

import re

from content_ai.evaluation.metrics.base import EvaluationMetric
from content_ai.evaluation.scoring.score import MetricResult
from content_ai.evaluation.snapshot import EvaluationSnapshot

_URL_RE = re.compile(r'https?://|www\.', re.IGNORECASE)
_REF_RE = re.compile(r'\[\d+\]|\(\d{4}\)|references?:', re.IGNORECASE)


class CitationsMetric(EvaluationMetric):
    name = 'citations'
    default_weight = 0.8

    def evaluate(self, snapshot: EvaluationSnapshot) -> MetricResult:
        text = snapshot.output_text or ''
        if not text.strip():
            return MetricResult(
                name=self.name,
                score=0.0,
                weight=self.default_weight,
                confidence=1.0,
                warnings=('Empty output.',),
                explanation='No text for citation scoring.',
            )
        has_url = bool(_URL_RE.search(text))
        has_ref = bool(_REF_RE.search(text))
        if has_url and has_ref:
            score = 0.95
            explanation = 'URLs and reference-like markers found.'
        elif has_url or has_ref:
            score = 0.7
            explanation = 'Some citation-like signals found.'
        else:
            score = 0.35
            explanation = 'No citation-like signals detected.'
        return MetricResult(
            name=self.name,
            score=score,
            weight=self.default_weight,
            confidence=0.5,
            explanation=explanation,
        )
