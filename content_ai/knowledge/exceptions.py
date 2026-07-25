"""Knowledge Engine exceptions (architecture-only, inactive in production)."""

from __future__ import annotations


class KnowledgeEngineError(Exception):
    """Base error for the Knowledge Engine."""


class ManifestError(KnowledgeEngineError):
    """Raised when the knowledge manifest is missing or invalid."""


class KnowledgeValidationError(KnowledgeEngineError):
    """Raised when knowledge metadata or files fail validation."""
