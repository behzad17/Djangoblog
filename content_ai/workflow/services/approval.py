"""Approval stage service (architecture stub)."""

from __future__ import annotations

from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class ApprovalService(WorkflowStageService):
    """Manage approval state. Does not publish."""

    name = 'approval'
    entry_state = WorkflowState.READY_FOR_APPROVAL
    success_state = WorkflowState.APPROVED

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.extension_data.setdefault('approval', {})
        context.extension_data['approval']['approved'] = True
        context.extension_data.setdefault('hooks', {})
        context.extension_data['hooks']['editorial_memory'] = 'pending'
        context.add_note('Approval recorded (stub); human remains responsible.')
        return context
