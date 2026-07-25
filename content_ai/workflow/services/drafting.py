"""Drafting stage service (RFC-003).

When ``context.extension_data['generation']`` is set, runs production
prompt assembly (PromptBuilder) and provider generation once.
Otherwise remains an architecture stub for inactive workflow demos.
"""

from __future__ import annotations

from content_ai.providers.exceptions import GenerationError
from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class DraftService(WorkflowStageService):
    """
    Generate the first AI draft.

    Production path: PromptBuilder once, then the configured provider.
    Stub path (no generation payload): placeholder text only.
    """

    name = 'drafting'
    entry_state = WorkflowState.RESEARCHING
    success_state = WorkflowState.DRAFTING

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.require_article_metadata('title')
        generation = context.extension_data.get('generation')
        if generation:
            return self._run_production(context, generation)
        return self._run_stub(context)

    def _run_stub(self, context: WorkflowContext) -> WorkflowContext:
        if not context.generated_draft:
            title = context.article_metadata.get('title', '')
            context.generated_draft = (
                f'[workflow-stub draft] {title}'.strip()
            )
            context.add_warning(
                'DraftService stub used; no generation payload provided.'
            )
        context.extension_data.setdefault('hooks', {})
        context.extension_data['hooks']['prompt_evaluation'] = 'pending'
        context.extension_data['hooks']['ai_provider'] = 'pending'
        return context

    def _run_production(
        self,
        context: WorkflowContext,
        generation: dict,
    ) -> WorkflowContext:
        # Lazy imports avoid circular imports and keep provider resolution
        # patchable via content_ai.providers.registry.get_provider.
        from content_ai.providers.registry import get_provider
        from content_ai.services.generation import build_generation_prompt

        task = generation['task']
        request = generation.get('request')
        provider_name = generation.get('provider_name')
        method_name = generation['method_name']

        prompt, prompt_version = build_generation_prompt(task, request)
        context.prompt_version = prompt_version or context.prompt_version
        context.extension_data['prompt_length'] = len(prompt or '')
        context.extension_data.setdefault('hooks', {})
        context.extension_data['hooks']['prompt_assembly'] = 'completed'

        provider = get_provider(provider_name or None)
        method = getattr(provider, method_name, None)
        if method is None:
            raise GenerationError(
                f"Provider '{provider.name}' does not support task '{task}'."
            )

        result = method(prompt)
        content = '' if result.content is None else str(result.content)
        context.generated_draft = content
        context.provider = result.provider or provider.name
        telemetry = result.telemetry
        if telemetry is not None:
            context.model = telemetry.model or context.model
            context.token_usage = telemetry.token_usage
            context.estimated_cost = telemetry.estimated_cost

        context.extension_data['generation_result'] = result
        context.extension_data['hooks']['ai_provider'] = 'completed'
        context.extension_data['hooks']['prompt_evaluation'] = 'pending'
        return context
