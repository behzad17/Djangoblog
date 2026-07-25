"""Metric package exports and default metric factories."""

from content_ai.evaluation.metrics.base import EvaluationMetric
from content_ai.evaluation.metrics.citations import CitationsMetric
from content_ai.evaluation.metrics.completeness import CompletenessMetric
from content_ai.evaluation.metrics.consistency import ConsistencyMetric
from content_ai.evaluation.metrics.length import OutputLengthMetric
from content_ai.evaluation.metrics.localisation import LocalisationMetric
from content_ai.evaluation.metrics.readability import ReadabilityMetric
from content_ai.evaluation.metrics.structure import StructureMetric


def default_metrics() -> list[EvaluationMetric]:
    return [
        ReadabilityMetric(),
        StructureMetric(),
        CompletenessMetric(),
        LocalisationMetric(),
        ConsistencyMetric(),
        CitationsMetric(),
        OutputLengthMetric(),
    ]


__all__ = [
    'CitationsMetric',
    'CompletenessMetric',
    'ConsistencyMetric',
    'EvaluationMetric',
    'LocalisationMetric',
    'OutputLengthMetric',
    'ReadabilityMetric',
    'StructureMetric',
    'default_metrics',
]
