"""Archive stage service (architecture stub)."""

from __future__ import annotations

from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class ArchiveService(WorkflowStageService):
    """Mark workflow context as archived. No storage backend yet."""

    name = 'archive'
    entry_state = WorkflowState.PUBLISHED
    success_state = WorkflowState.ARCHIVED

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.extension_data.setdefault('archive', {})
        context.extension_data['archive']['archived'] = True
        context.add_note('Workflow archived (stub).')
        return context
