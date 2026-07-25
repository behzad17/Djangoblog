"""AI evaluation framework exceptions (RFC-004)."""

from __future__ import annotations


class EvaluationError(Exception):
    """Base error for the AI evaluation framework."""


class MetricError(EvaluationError):
    """Raised when a metric fails or is misconfigured."""


class ComparisonError(EvaluationError):
    """Raised when snapshot comparison cannot proceed."""


class ReportError(EvaluationError):
    """Raised when report generation fails."""


class SnapshotError(EvaluationError):
    """Raised when an evaluation snapshot is invalid."""


class RegistryError(EvaluationError):
    """Raised for metric registry registration/discovery errors."""
