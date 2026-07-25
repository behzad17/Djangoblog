"""Placeholder stage services for future RFCs."""

from __future__ import annotations

from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class FactCheckPlaceholderService(WorkflowStageService):
    """RFC-007 hook: pass through without fact-checking logic."""

    name = 'fact_check_placeholder'
    entry_state = WorkflowState.FACT_CHECK_PENDING
    success_state = WorkflowState.REVIEWING

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.extension_data.setdefault('hooks', {})
        context.extension_data['hooks']['fact_checking'] = 'skipped_placeholder'
        context.add_note('Fact check placeholder — no validation performed.')
        return context


class RevisionService(WorkflowStageService):
    """Return a revision cycle to drafting without rewriting content."""

    name = 'revision'
    entry_state = WorkflowState.REVISION_REQUIRED
    success_state = WorkflowState.DRAFTING

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.add_note('Revision requested; returning toward drafting.')
        context.extension_data.setdefault('hooks', {})
        context.extension_data['hooks']['ai_agents'] = 'pending'
        return context
