"""Drafting stage service (architecture stub)."""

from __future__ import annotations

from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class DraftService(WorkflowStageService):
    """
    Generate the first AI draft.

    Stub only: does not call EditorialAIService, PromptBuilder, or OpenAI.
    Future RFCs may wire real generation behind an explicit migration.
    """

    name = 'drafting'
    entry_state = WorkflowState.RESEARCHING
    success_state = WorkflowState.DRAFTING

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.require_article_metadata('title')
        if not context.generated_draft:
            title = context.article_metadata.get('title', '')
            context.generated_draft = (
                f'[workflow-stub draft] {title}'.strip()
            )
            context.add_warning(
                'DraftService stub used; production generation unchanged.'
            )
        context.extension_data.setdefault('hooks', {})
        context.extension_data['hooks']['prompt_evaluation'] = 'pending'
        context.extension_data['hooks']['ai_provider'] = 'pending'
        return context
