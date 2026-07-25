"""Claim types, statuses, and Claim model (RFC-007)."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any
from uuid import uuid4

from content_ai.fact_check.exceptions import ConfidenceError, ValidationError

if TYPE_CHECKING:
    from content_ai.fact_check.evidence import Evidence


class ClaimType(str, Enum):
    """Supported claim categories. Future types register via the registry."""

    NUMERICAL = 'numerical'
    DATE = 'date'
    STATISTIC = 'statistic'
    LOCATION = 'location'
    PERSON = 'person'
    ORGANISATION = 'organisation'
    TITLE = 'title'
    GOVERNMENT_DECISION = 'government_decision'
    LEGAL_REFERENCE = 'legal_reference'
    SCIENTIFIC = 'scientific'
    MEDICAL = 'medical'
    FINANCIAL = 'financial'
    HISTORICAL = 'historical'
    GENERAL = 'general'


class VerificationStatus(str, Enum):
    """
    Verification outcomes.

    These never auto-approve publication — editors decide.
    """

    UNVERIFIED = 'unverified'
    SUPPORTED = 'supported'
    PARTIALLY_SUPPORTED = 'partially_supported'
    CONFLICTING = 'conflicting'
    INSUFFICIENT_EVIDENCE = 'insufficient_evidence'
    OUTDATED = 'outdated'
    REQUIRES_EDITOR_REVIEW = 'requires_editor_review'


class ConfidenceLevel(str, Enum):
    """Qualitative confidence. Numeric scores may come later (no ML here)."""

    HIGH = 'high'
    MEDIUM = 'medium'
    LOW = 'low'
    UNKNOWN = 'unknown'


@dataclass(frozen=True, slots=True)
class Claim:
    """Provider-independent factual claim extracted or supplied for checking."""

    claim_id: str
    claim_text: str
    claim_type: ClaimType = ClaimType.GENERAL
    entity: str = ''
    category: str = ''
    detected_language: str = ''
    evidence: tuple[Evidence, ...] = ()
    confidence: ConfidenceLevel = ConfidenceLevel.UNKNOWN
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED
    warnings: tuple[str, ...] = ()
    metadata: dict[str, Any] = field(default_factory=dict)


def coerce_confidence(value: ConfidenceLevel | str) -> ConfidenceLevel:
    if isinstance(value, ConfidenceLevel):
        return value
    try:
        return ConfidenceLevel(str(value))
    except ValueError as exc:
        raise ConfidenceError(
            f'Invalid confidence value: {value!r}.'
        ) from exc


def coerce_claim_type(value: ClaimType | str) -> ClaimType:
    if isinstance(value, ClaimType):
        return value
    try:
        return ClaimType(str(value))
    except ValueError as exc:
        raise ValidationError(
            f'Unsupported claim type: {value!r}.'
        ) from exc


def coerce_status(value: VerificationStatus | str) -> VerificationStatus:
    if isinstance(value, VerificationStatus):
        return value
    try:
        return VerificationStatus(str(value))
    except ValueError as exc:
        raise ValidationError(
            f'Invalid verification status: {value!r}.'
        ) from exc


def create_claim(
    *,
    claim_text: str,
    claim_type: ClaimType | str = ClaimType.GENERAL,
    entity: str = '',
    category: str = '',
    detected_language: str = '',
    evidence: list[Evidence] | None = None,
    confidence: ConfidenceLevel | str = ConfidenceLevel.UNKNOWN,
    verification_status: VerificationStatus | str = (
        VerificationStatus.UNVERIFIED
    ),
    warnings: list[str] | None = None,
    claim_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> Claim:
    text = (claim_text or '').strip()
    if not text:
        raise ValidationError('claim_text must be a non-empty string.')
    cid = (claim_id or str(uuid4())).strip()
    if not cid:
        raise ValidationError('claim_id must be non-empty.')
    return Claim(
        claim_id=cid,
        claim_text=text,
        claim_type=coerce_claim_type(claim_type),
        entity=entity or '',
        category=category or '',
        detected_language=detected_language or '',
        evidence=tuple(evidence or ()),
        confidence=coerce_confidence(confidence),
        verification_status=coerce_status(verification_status),
        warnings=tuple(warnings or ()),
        metadata=dict(metadata or {}),
    )


def validate_claim(claim: Claim) -> None:
    from content_ai.fact_check.evidence import validate_evidence
    from content_ai.fact_check.confidence import validate_confidence

    if claim is None:
        raise ValidationError('Claim is required.')
    if not claim.claim_text.strip():
        raise ValidationError('Empty claims are not allowed.')
    if not isinstance(claim.claim_type, ClaimType):
        raise ValidationError(f'Unsupported claim type: {claim.claim_type!r}.')
    if not isinstance(claim.verification_status, VerificationStatus):
        raise ValidationError(
            f'Invalid verification status: {claim.verification_status!r}.'
        )
    validate_confidence(claim.confidence)
    for item in claim.evidence:
        validate_evidence(item)
