"""Verification pipeline stubs (RFC-007). No external retrieval."""

from __future__ import annotations

from dataclasses import replace

from content_ai.fact_check.claims import (
    Claim,
    ConfidenceLevel,
    VerificationStatus,
    create_claim,
    validate_claim,
)
from content_ai.fact_check.confidence import summarise_evidence_confidence
from content_ai.fact_check.exceptions import (
    ClaimExtractionError,
    VerificationError,
)
from content_ai.fact_check.registry import FactCheckRegistry, build_default_registry


def extract_claims(text: str) -> list[Claim]:
    """
    Extract claims from text.

    Stub: treats non-empty paragraphs as GENERAL claims.
    Automatic NLP extraction is reserved for a future RFC.
    """
    body = (text or '').strip()
    if not body:
        raise ClaimExtractionError('Cannot extract claims from empty text.')
    claims: list[Claim] = []
    for block in body.split('\n\n'):
        piece = block.strip()
        if piece:
            claims.append(create_claim(claim_text=piece, claim_type='general'))
    if not claims:
        raise ClaimExtractionError('No claims could be extracted.')
    return claims


def identify_entities(claim: Claim) -> Claim:
    """Stub entity identification — copies a simple heuristic into metadata."""
    validate_claim(claim)
    entity = claim.entity
    if not entity:
        # Very light heuristic: first Capitalised token sequence.
        tokens = claim.claim_text.split()
        caps = [t for t in tokens if t[:1].isupper()]
        entity = ' '.join(caps[:3])
    meta = dict(claim.metadata)
    meta['entities_identified'] = True
    return replace(claim, entity=entity, metadata=meta)


def retrieve_evidence(
    claim: Claim,
    registry: FactCheckRegistry | None = None,
) -> Claim:
    """
    Attach evidence via registered providers.

    Default provider returns no evidence (no external retrieval).
    """
    validate_claim(claim)
    reg = registry or build_default_registry()
    found = reg.collect_evidence(claim)
    if not found:
        return replace(
            claim,
            warnings=tuple(
                list(claim.warnings)
                + ['Evidence retrieval stub returned no sources.']
            ),
        )
    return replace(claim, evidence=tuple(list(claim.evidence) + found))


def compare_evidence(claim: Claim) -> Claim:
    """Stub comparison — marks insufficient evidence when none present."""
    validate_claim(claim)
    if not claim.evidence:
        return replace(
            claim,
            verification_status=VerificationStatus.INSUFFICIENT_EVIDENCE,
        )
    # Multiple sources with conflicting excerpts would be future work.
    return replace(
        claim,
        verification_status=VerificationStatus.REQUIRES_EDITOR_REVIEW,
        warnings=tuple(
            list(claim.warnings)
            + ['Evidence comparison is a stub; editor review required.']
        ),
    )


def calculate_confidence(claim: Claim) -> Claim:
    levels = [item.confidence for item in claim.evidence]
    summary = summarise_evidence_confidence(levels)
    if not claim.evidence:
        summary = ConfidenceLevel.UNKNOWN
    return replace(claim, confidence=summary)


class Verifier:
    """
    Run the verification pipeline for one claim.

    Extract → entities → evidence → compare → confidence → rules.
    Does not publish or auto-approve.
    """

    def __init__(self, registry: FactCheckRegistry | None = None):
        self.registry = registry or build_default_registry()

    def verify(self, claim: Claim) -> Claim:
        try:
            validate_claim(claim)
            current = identify_entities(claim)
            self.registry.run_validators(current)
            current = retrieve_evidence(current, self.registry)
            current = compare_evidence(current)
            current = calculate_confidence(current)
            current = self.registry.apply_rules(current)
            return current
        except (ClaimExtractionError, VerificationError):
            raise
        except Exception as exc:
            raise VerificationError(f'Verification failed: {exc}') from exc

    def verify_many(self, claims: list[Claim]) -> list[Claim]:
        return [self.verify(claim) for claim in claims]
