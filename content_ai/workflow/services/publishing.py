"""Publishing preparation service (architecture stub)."""

from __future__ import annotations

from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.exceptions import StageExecutionError
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class PublishingService(WorkflowStageService):
    """
    Prepare publication artefacts only.

    Does NOT create Blog posts, call publishers, or auto-publish.
    """

    name = 'publishing'
    entry_state = WorkflowState.APPROVED
    success_state = WorkflowState.PUBLISHED

    def run(self, context: WorkflowContext) -> WorkflowContext:
        if not context.generated_draft:
            raise StageExecutionError(
                'Cannot prepare publishing without a generated draft.'
            )
        context.extension_data.setdefault('publishing', {})
        context.extension_data['publishing']['prepared'] = True
        context.extension_data['publishing']['auto_publish'] = False
        context.add_warning(
            'PublishingService prepares metadata only; no publish side effects.'
        )
        return context
