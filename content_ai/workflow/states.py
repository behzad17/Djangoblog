"""Editorial workflow states and allowed transitions (RFC-003)."""

from __future__ import annotations

from enum import Enum


class WorkflowState(str, Enum):
    """Explicit states for the AI editorial lifecycle."""

    IDEA = 'idea'
    RESEARCHING = 'researching'
    DRAFTING = 'drafting'
    FACT_CHECK_PENDING = 'fact_check_pending'
    REVIEWING = 'reviewing'
    REVISION_REQUIRED = 'revision_required'
    READY_FOR_APPROVAL = 'ready_for_approval'
    APPROVED = 'approved'
    PUBLISHED = 'published'
    ARCHIVED = 'archived'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


# Allowed directed transitions. Future RFCs may extend this map carefully.
ALLOWED_TRANSITIONS: dict[WorkflowState, frozenset[WorkflowState]] = {
    WorkflowState.IDEA: frozenset({
        WorkflowState.RESEARCHING,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    }),
    WorkflowState.RESEARCHING: frozenset({
        WorkflowState.DRAFTING,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    }),
    WorkflowState.DRAFTING: frozenset({
        WorkflowState.FACT_CHECK_PENDING,
        WorkflowState.REVIEWING,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    }),
    WorkflowState.FACT_CHECK_PENDING: frozenset({
        WorkflowState.REVIEWING,
        WorkflowState.REVISION_REQUIRED,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    }),
    WorkflowState.REVIEWING: frozenset({
        WorkflowState.REVISION_REQUIRED,
        WorkflowState.READY_FOR_APPROVAL,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    }),
    WorkflowState.REVISION_REQUIRED: frozenset({
        WorkflowState.DRAFTING,
        WorkflowState.REVIEWING,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    }),
    WorkflowState.READY_FOR_APPROVAL: frozenset({
        WorkflowState.APPROVED,
        WorkflowState.REVISION_REQUIRED,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    }),
    WorkflowState.APPROVED: frozenset({
        WorkflowState.PUBLISHED,
        WorkflowState.CANCELLED,
        WorkflowState.FAILED,
    }),
    WorkflowState.PUBLISHED: frozenset({
        WorkflowState.ARCHIVED,
        WorkflowState.FAILED,
    }),
    WorkflowState.ARCHIVED: frozenset(),
    WorkflowState.FAILED: frozenset(),
    WorkflowState.CANCELLED: frozenset(),
}


def can_transition(current: WorkflowState, target: WorkflowState) -> bool:
    """Return True if ``current`` → ``target`` is allowed."""
    return target in ALLOWED_TRANSITIONS.get(current, frozenset())
