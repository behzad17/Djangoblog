"""Editorial workflow package (RFC-003).

Inactive architecture for the AI-assisted editorial lifecycle.
Does not change production generation or publishing.
"""

from content_ai.workflow.context import StageLogEntry, WorkflowContext
from content_ai.workflow.exceptions import (
    ContextError,
    StageExecutionError,
    TransitionError,
    WorkflowError,
    WorkflowValidationError,
)
from content_ai.workflow.orchestrator import (
    WorkflowOrchestrator,
    create_initial_context,
    default_stages,
)
from content_ai.workflow.states import (
    ALLOWED_TRANSITIONS,
    WorkflowState,
    can_transition,
)

__all__ = [
    'ALLOWED_TRANSITIONS',
    'ContextError',
    'StageExecutionError',
    'StageLogEntry',
    'TransitionError',
    'WorkflowContext',
    'WorkflowError',
    'WorkflowOrchestrator',
    'WorkflowState',
    'WorkflowValidationError',
    'can_transition',
    'create_initial_context',
    'default_stages',
]
