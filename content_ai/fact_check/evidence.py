"""Evidence model (RFC-007)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import uuid4

from content_ai.fact_check.claims import ConfidenceLevel, coerce_confidence
from content_ai.fact_check.confidence import validate_confidence
from content_ai.fact_check.exceptions import EvidenceError


@dataclass(frozen=True, slots=True)
class Evidence:
    """
    One piece of evidence for a claim.

    Designed to integrate later with Source Intelligence (RFC-006).
    """

    evidence_id: str
    source: str = ''
    url: str = ''
    publisher: str = ''
    publication_date: date | None = None
    evidence_type: str = ''
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    excerpt: str = ''
    metadata: dict[str, Any] = field(default_factory=dict)


def create_evidence(
    *,
    source: str = '',
    url: str = '',
    publisher: str = '',
    publication_date: date | None = None,
    evidence_type: str = '',
    confidence: ConfidenceLevel | str = ConfidenceLevel.UNKNOWN,
    excerpt: str = '',
    evidence_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Evidence:
    eid = (evidence_id or str(uuid4())).strip()
    if not eid:
        raise EvidenceError('evidence_id must be non-empty.')
    return Evidence(
        evidence_id=eid,
        source=source or '',
        url=url or '',
        publisher=publisher or '',
        publication_date=publication_date,
        evidence_type=evidence_type or '',
        confidence=coerce_confidence(confidence),
        excerpt=excerpt or '',
        metadata=dict(metadata or {}),
    )


def validate_evidence(evidence: Evidence) -> None:
    if evidence is None:
        raise EvidenceError('Evidence is required.')
    if not evidence.evidence_id:
        raise EvidenceError('Evidence is missing evidence_id.')
    validate_confidence(evidence.confidence)
