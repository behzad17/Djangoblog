"""AI evaluation package.

Includes:
- Human editorial feedback collection (existing production feature)
- Passive AI Evaluation Framework (RFC-004) — metrics/snapshots/reports
"""

from content_ai.evaluation.comparison import ComparisonEngine, ComparisonResult
from content_ai.evaluation.constants import AIFeedbackRating, AIFeedbackReason
from content_ai.evaluation.evaluator import EvaluationResult, Evaluator
from content_ai.evaluation.exceptions import (
    ComparisonError,
    EvaluationError,
    MetricError,
    RegistryError,
    ReportError,
    SnapshotError,
)
from content_ai.evaluation.models import AIGenerationFeedback
from content_ai.evaluation.registry import MetricRegistry, build_default_registry
from content_ai.evaluation.report import EvaluationReport, ReportBuilder
from content_ai.evaluation.scoring import AggregateScore, MetricResult, aggregate_scores
from content_ai.evaluation.services import FeedbackService, FeedbackValidationError
from content_ai.evaluation.snapshot import (
    EvaluationSnapshot,
    create_snapshot,
    validate_snapshot,
)

__all__ = [
    'AIFeedbackRating',
    'AIFeedbackReason',
    'AIGenerationFeedback',
    'AggregateScore',
    'ComparisonEngine',
    'ComparisonError',
    'ComparisonResult',
    'EvaluationError',
    'EvaluationReport',
    'EvaluationResult',
    'EvaluationSnapshot',
    'Evaluator',
    'FeedbackService',
    'FeedbackValidationError',
    'MetricError',
    'MetricRegistry',
    'MetricResult',
    'RegistryError',
    'ReportBuilder',
    'ReportError',
    'SnapshotError',
    'aggregate_scores',
    'build_default_registry',
    'create_snapshot',
    'validate_snapshot',
]
