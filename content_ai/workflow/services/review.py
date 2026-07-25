"""Review stage service (architecture stub)."""

from __future__ import annotations

from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class ReviewService(WorkflowStageService):
    """Collect editorial feedback placeholders. No fact-check/SEO logic."""

    name = 'review'
    entry_state = WorkflowState.REVIEWING
    success_state = WorkflowState.READY_FOR_APPROVAL

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.extension_data.setdefault('review', {})
        context.extension_data['review'].setdefault('feedback', [])
        context.extension_data.setdefault('hooks', {})
        # Future: RFC-007 Fact Checking, RFC-008 SEO, RFC-009 Feedback.
        context.extension_data['hooks']['fact_checking'] = 'pending'
        context.extension_data['hooks']['seo_intelligence'] = 'pending'
        context.extension_data['hooks']['feedback_learning'] = 'pending'
        context.add_note('Editorial review placeholder completed (stub).')
        return context
