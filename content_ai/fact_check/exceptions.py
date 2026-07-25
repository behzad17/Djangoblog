"""Fact checking framework exceptions (RFC-007)."""

from __future__ import annotations


class FactCheckError(Exception):
    """Base error for the fact checking framework."""


class ClaimExtractionError(FactCheckError):
    """Raised when claim extraction fails."""


class EvidenceError(FactCheckError):
    """Raised for evidence model or retrieval issues."""


class VerificationError(FactCheckError):
    """Raised when verification cannot complete."""


class ConfidenceError(FactCheckError):
    """Raised for invalid confidence values."""


class RegistryError(FactCheckError):
    """Raised for claim-type / rule / provider registry errors."""


class ValidationError(FactCheckError):
    """Raised when fact-check inputs or configuration are invalid."""
