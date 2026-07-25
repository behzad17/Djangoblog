"""Editorial workflow exceptions (RFC-003)."""

from __future__ import annotations


class WorkflowError(Exception):
    """Base error for the editorial workflow layer."""


class StageExecutionError(WorkflowError):
    """Raised when a workflow stage fails during execution."""


class TransitionError(WorkflowError):
    """Raised for illegal or unknown state transitions."""


class WorkflowValidationError(WorkflowError):
    """Raised when workflow configuration or inputs are invalid."""


class ContextError(WorkflowError):
    """Raised when WorkflowContext is missing or incomplete."""
