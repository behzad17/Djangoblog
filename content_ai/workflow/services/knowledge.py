"""Knowledge preparation workflow stage (RFC-002 / RFC-002.5)."""

from __future__ import annotations

from content_ai.config import DEFAULT_STYLE
from content_ai.knowledge.integration import prepare_knowledge_for_context
from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class KnowledgeService(WorkflowStageService):
    """
    Prepare Knowledge Engine metadata before drafting.

    Soft-fails: never blocks generation. Injection (when flagged) happens
    in DraftService after PromptBuilder assembles the prompt.
    """

    name = 'knowledge'
    entry_state = WorkflowState.RESEARCHING
    success_state = WorkflowState.RESEARCHING

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.extension_data.setdefault('hooks', {})
        generation = context.extension_data.get('generation') or {}
        request = generation.get('request')
        user_prompt = context.article_metadata.get('title', '') or ''
        if request is not None:
            instructions = getattr(request, 'instructions', '') or ''
            if instructions:
                user_prompt = f'{user_prompt}\n{instructions}'.strip()

        payload = prepare_knowledge_for_context(
            user_prompt=user_prompt,
            style=DEFAULT_STYLE,
            language=context.language or '',
        )
        context.extension_data['knowledge'] = payload
        status = payload.get('status') or 'skipped'
        if status == 'prepared':
            version = payload.get('knowledge_version') or ''
            if version:
                context.knowledge_version = version
            context.extension_data['hooks']['knowledge_retrieval'] = 'completed'
        elif status == 'failed_soft':
            context.add_warning(
                f"Knowledge preparation skipped: {payload.get('error', '')}"
            )
            context.extension_data['hooks']['knowledge_retrieval'] = 'failed_soft'
        else:
            context.extension_data['hooks']['knowledge_retrieval'] = 'skipped'
        return context
