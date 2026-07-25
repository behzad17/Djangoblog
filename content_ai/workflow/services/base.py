"""Base interface for editorial workflow stage services."""

from __future__ import annotations

from abc import ABC, abstractmethod

from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.states import WorkflowState


class WorkflowStageService(ABC):
    """
    Consistent interface for workflow stage services.

    Implementations should be lightweight. Do not call other stages.
    """

    name: str = ''
    entry_state: WorkflowState | None = None
    success_state: WorkflowState | None = None

    @abstractmethod
    def run(self, context: WorkflowContext) -> WorkflowContext:
        """Execute this stage and return the updated context."""
