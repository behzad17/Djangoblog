"""Confidence helpers (RFC-007). No ML."""

from __future__ import annotations

from content_ai.fact_check.claims import ConfidenceLevel
from content_ai.fact_check.exceptions import ConfidenceError


def validate_confidence(level: ConfidenceLevel) -> None:
    if not isinstance(level, ConfidenceLevel):
        raise ConfidenceError(f'Invalid confidence value: {level!r}.')


def confidence_rank(level: ConfidenceLevel) -> int:
    """Ordinal rank for comparisons (higher is more confident)."""
    order = {
        ConfidenceLevel.UNKNOWN: 0,
        ConfidenceLevel.LOW: 1,
        ConfidenceLevel.MEDIUM: 2,
        ConfidenceLevel.HIGH: 3,
    }
    validate_confidence(level)
    return order[level]


def summarise_evidence_confidence(
    levels: list[ConfidenceLevel],
) -> ConfidenceLevel:
    """
    Conservative summary: lowest non-unknown when present, else UNKNOWN.
    """
    if not levels:
        return ConfidenceLevel.UNKNOWN
    known = [level for level in levels if level != ConfidenceLevel.UNKNOWN]
    if not known:
        return ConfidenceLevel.UNKNOWN
    return min(known, key=confidence_rank)
