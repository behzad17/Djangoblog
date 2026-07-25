"""Fact checking framework package (RFC-007).

Passive architecture: assists editors; never auto-publishes or adjudicates truth.
"""

from content_ai.fact_check.checker import FactChecker
from content_ai.fact_check.claims import (
    Claim,
    ClaimType,
    ConfidenceLevel,
    VerificationStatus,
    create_claim,
    validate_claim,
)
from content_ai.fact_check.confidence import (
    confidence_rank,
    summarise_evidence_confidence,
    validate_confidence,
)
from content_ai.fact_check.evidence import (
    Evidence,
    create_evidence,
    validate_evidence,
)
from content_ai.fact_check.exceptions import (
    ClaimExtractionError,
    ConfidenceError,
    EvidenceError,
    FactCheckError,
    RegistryError,
    ValidationError,
    VerificationError,
)
from content_ai.fact_check.registry import (
    FactCheckRegistry,
    build_default_registry,
)
from content_ai.fact_check.report import (
    ClaimReport,
    FactCheckReport,
    build_claim_report,
    build_fact_check_report,
)
from content_ai.fact_check.verifier import Verifier, extract_claims

__all__ = [
    'Claim',
    'ClaimExtractionError',
    'ClaimReport',
    'ClaimType',
    'ConfidenceError',
    'ConfidenceLevel',
    'Evidence',
    'EvidenceError',
    'FactCheckError',
    'FactCheckRegistry',
    'FactCheckReport',
    'FactChecker',
    'RegistryError',
    'ValidationError',
    'VerificationError',
    'VerificationStatus',
    'Verifier',
    'build_claim_report',
    'build_default_registry',
    'build_fact_check_report',
    'confidence_rank',
    'create_claim',
    'create_evidence',
    'extract_claims',
    'summarise_evidence_confidence',
    'validate_claim',
    'validate_confidence',
    'validate_evidence',
]
