"""Editorial workflow package (RFC-003).

Production generation is coordinated by WorkflowOrchestrator.execute().
Does not auto-publish Blog posts.
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
    PRODUCTION_GENERATION_STAGES,
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
    'PRODUCTION_GENERATION_STAGES',
]
