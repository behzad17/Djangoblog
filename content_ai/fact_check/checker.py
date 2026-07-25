"""High-level fact checker facade (RFC-007)."""

from __future__ import annotations

from content_ai.fact_check.claims import Claim
from content_ai.fact_check.exceptions import ValidationError
from content_ai.fact_check.registry import FactCheckRegistry, build_default_registry
from content_ai.fact_check.report import FactCheckReport, build_fact_check_report
from content_ai.fact_check.verifier import Verifier, extract_claims


class FactChecker:
    """
    Orchestrate extract → verify → report.

    Passive: no external APIs, no auto-publish, no truth adjudication.
    """

    def __init__(self, registry: FactCheckRegistry | None = None):
        self.registry = registry or build_default_registry()
        self.verifier = Verifier(registry=self.registry)

    def check_text(self, text: str) -> FactCheckReport:
        claims = extract_claims(text)
        return self.check_claims(claims)

    def check_claims(self, claims: list[Claim]) -> FactCheckReport:
        if not claims:
            raise ValidationError('No claims provided.')
        # Duplicate claim text detection (same normalised text).
        seen: set[str] = set()
        unique: list[Claim] = []
        for claim in claims:
            key = claim.claim_text.casefold().strip()
            if key in seen:
                raise ValidationError(
                    f'Duplicate claim text: {claim.claim_text!r}.'
                )
            seen.add(key)
            unique.append(claim)
        verified = self.verifier.verify_many(unique)
        return build_fact_check_report(verified)
