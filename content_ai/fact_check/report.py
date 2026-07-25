"""Structured fact-check reports (RFC-007)."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from content_ai.fact_check.claims import Claim, validate_claim
from content_ai.fact_check.exceptions import ValidationError


@dataclass(frozen=True, slots=True)
class ClaimReport:
    """Machine-readable report for a single claim."""

    claim_id: str
    claim_text: str
    verification_status: str
    confidence: str
    evidence: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    editorial_recommendation: str = ''
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class FactCheckReport:
    """Aggregate report for a set of claims."""

    claims: tuple[ClaimReport, ...]
    summary: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            'claims': [item.to_dict() for item in self.claims],
            'summary': dict(self.summary),
            'metadata': dict(self.metadata),
        }


def _recommendation(claim: Claim) -> str:
    status = claim.verification_status.value
    mapping = {
        'supported': 'Looks supported by attached evidence; still review before publish.',
        'partially_supported': 'Only partially supported — verify missing pieces.',
        'conflicting': 'Evidence conflicts — resolve before publish.',
        'insufficient_evidence': 'Insufficient evidence — do not treat as verified.',
        'outdated': 'Evidence may be outdated — refresh sources.',
        'requires_editor_review': 'Requires human editorial review.',
        'unverified': 'Unverified — do not publish as fact-checked.',
    }
    return mapping.get(status, 'Requires human editorial review.')


def build_claim_report(claim: Claim) -> ClaimReport:
    validate_claim(claim)
    evidence_payload = [
        {
            'evidence_id': item.evidence_id,
            'source': item.source,
            'url': item.url,
            'publisher': item.publisher,
            'publication_date': (
                item.publication_date.isoformat()
                if item.publication_date
                else None
            ),
            'evidence_type': item.evidence_type,
            'confidence': item.confidence.value,
            'excerpt': item.excerpt,
            'metadata': dict(item.metadata),
        }
        for item in claim.evidence
    ]
    return ClaimReport(
        claim_id=claim.claim_id,
        claim_text=claim.claim_text,
        verification_status=claim.verification_status.value,
        confidence=claim.confidence.value,
        evidence=evidence_payload,
        warnings=list(claim.warnings),
        editorial_recommendation=_recommendation(claim),
        metadata=dict(claim.metadata),
    )


def build_fact_check_report(claims: list[Claim]) -> FactCheckReport:
    if not claims:
        raise ValidationError('Cannot build a report from zero claims.')
    reports = tuple(build_claim_report(claim) for claim in claims)
    counts: dict[str, int] = {}
    for item in reports:
        counts[item.verification_status] = (
            counts.get(item.verification_status, 0) + 1
        )
    return FactCheckReport(
        claims=reports,
        summary={
            'claim_count': len(reports),
            'status_counts': counts,
            'auto_publish_allowed': False,
        },
        metadata={
            'passive': True,
            'human_decision_required': True,
        },
    )
