"""Research stage service (architecture stub)."""

from __future__ import annotations

from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class ResearchService(WorkflowStageService):
    """Prepare research inputs. Does not call providers or knowledge RAG."""

    name = 'research'
    entry_state = WorkflowState.IDEA
    success_state = WorkflowState.RESEARCHING

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.require_article_metadata('title')
        context.extension_data.setdefault('research', {})
        context.extension_data['research']['prepared'] = True
        context.add_note('Research inputs prepared (stub).')
        # Knowledge retrieval hook point (RFC-002 / future RAG) — inactive.
        context.extension_data.setdefault('hooks', {})
        context.extension_data['hooks']['knowledge_retrieval'] = 'pending'
        return context
