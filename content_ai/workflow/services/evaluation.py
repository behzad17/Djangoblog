"""Evaluation hook workflow stage (RFC-004)."""

from __future__ import annotations

from content_ai.config.ai_engine import ENABLE_AI_EVALUATION_FRAMEWORK
from content_ai.workflow.context import WorkflowContext
from content_ai.workflow.services.base import WorkflowStageService
from content_ai.workflow.states import WorkflowState


class EvaluationHookService(WorkflowStageService):
    """
    Stable evaluation stage after drafting.

    When the evaluation flag is off, records a skipped hook only.
    Soft-fails: never blocks generation results.
    """

    name = 'evaluation'
    entry_state = WorkflowState.DRAFTING
    success_state = WorkflowState.DRAFTING

    def run(self, context: WorkflowContext) -> WorkflowContext:
        context.extension_data.setdefault('hooks', {})
        if not ENABLE_AI_EVALUATION_FRAMEWORK:
            context.extension_data['evaluation'] = {'status': 'skipped'}
            context.extension_data['hooks']['prompt_evaluation'] = 'skipped'
            return context

        try:
            from content_ai.evaluation import Evaluator, create_snapshot

            generation = context.extension_data.get('generation') or {}
            request = generation.get('request')
            input_text = context.article_metadata.get('title', '') or ''
            if request is not None:
                instructions = getattr(request, 'instructions', '') or ''
                if instructions:
                    input_text = f'{input_text}\n{instructions}'.strip()

            snap = create_snapshot(
                output_text=context.generated_draft or '',
                input_text=input_text,
                workflow_stage=context.state.value,
                prompt_version=context.prompt_version,
                knowledge_version=context.knowledge_version,
                provider=context.provider,
                model=context.model,
                language=context.language,
                token_usage=context.token_usage,
                estimated_cost=context.estimated_cost,
                latency_ms=context.execution_time_ms,
                warnings=list(context.warnings),
            )
            result = Evaluator().evaluate(snap)
            context.extension_data['evaluation'] = {
                'status': 'completed',
                'overall_score': result.aggregate.overall_score,
                'weighted_score': result.aggregate.weighted_score,
                'scores': dict(result.snapshot.scores),
            }
            context.extension_data['hooks']['prompt_evaluation'] = 'completed'
        except Exception as exc:  # noqa: BLE001 — soft-fail evaluation
            context.add_warning(f'Evaluation hook skipped: {exc}')
            context.extension_data['evaluation'] = {
                'status': 'failed_soft',
                'error': str(exc),
            }
            context.extension_data['hooks']['prompt_evaluation'] = 'failed_soft'
        return context
