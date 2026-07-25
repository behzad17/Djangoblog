"""Exceptions for the inactive AI Engine prompt builder / validator."""

from __future__ import annotations


class AIEnginePromptError(Exception):
    """Base error for AI Engine prompt architecture."""


class UnknownPromptVersionError(AIEnginePromptError):
    """Raised when a prompt version is not supported or missing on disk."""


class UnknownStyleError(AIEnginePromptError):
    """Raised when a style id is not supported or missing on disk."""


class MissingPromptModuleError(AIEnginePromptError):
    """Raised when a required system or style module file is missing."""


class InvalidPromptStructureError(AIEnginePromptError):
    """Raised when assembled prompt structure fails validation."""
