"""Single orchestration entry point for Content AI generation."""

import time

from content_ai.config import DEFAULT_PROMPT_VERSION, DEFAULT_STYLE
from content_ai.constants import AIGenerationTask
from content_ai.prompts.builders import PromptBuilder
from content_ai.prompts.registry import get_prompt_template
from content_ai.providers.exceptions import GenerationError, ProviderError
from content_ai.schemas.responses import GenerationResult
from content_ai.telemetry import (
    AIExecutionTelemetry,
    attach_telemetry,
    merge_telemetry,
    utc_now,
)
from content_ai.workflow import (
    StageExecutionError,
    WorkflowOrchestrator,
    create_initial_context,
)

# Maps generation tasks to BaseAIProvider method names.
_TASK_METHODS = {
    AIGenerationTask.POST_GENERATION: 'generate_post',
    AIGenerationTask.AD_GENERATION: 'generate_ad',
    AIGenerationTask.REWRITE: 'rewrite',
    AIGenerationTask.SUMMARY: 'summarize',
    AIGenerationTask.TRANSLATION: 'translate',
}


def build_generation_prompt(task, request=None):
    """
    Assemble the production prompt via PromptBuilder.

    Task asset templates (post/ads) supply the user-prompt section only.
    PromptBuilder is the sole assembler of the final prompt string.
    """
    template = get_prompt_template(task)
    user_prompt = template.build(request)
    prompt = PromptBuilder().build(
        version=DEFAULT_PROMPT_VERSION,
        style=DEFAULT_STYLE,
        user_prompt=user_prompt,
    )
    return prompt, DEFAULT_PROMPT_VERSION


def _title_for_request(task, request=None) -> str:
    if request is not None:
        for attr in ('title', 'business_name'):
            value = getattr(request, attr, None)
            if value and str(value).strip():
                return str(value).strip()
    return str(task)


class ContentGenerationService:
    """
    Orchestrates AI generation via WorkflowOrchestrator.

    Flow: request → WorkflowOrchestrator.execute() → research → drafting
    (PromptBuilder once → provider) → GenerationResult.
    Measures execution timing and attaches ``AIExecutionTelemetry``.
    No validation, persistence, or business logic.
    """

    def __init__(self, workflow: WorkflowOrchestrator | None = None):
        self.workflow = workflow or WorkflowOrchestrator()

    def generate(self, task, request=None, provider_name=None):
        """
        Run ``task`` through WorkflowOrchestrator against the configured provider.

        ``request`` should be a canonical request schema (e.g.
        ``PostGenerationRequest`` / ``AdGenerationRequest``) when applicable.
        ``provider_name`` optionally overrides ``settings.CONTENT_AI_PROVIDER``.
        """
        method_name = _TASK_METHODS.get(task)
        if method_name is None:
            raise GenerationError(f"Unsupported generation task: '{task}'.")

        language = ''
        if request is not None:
            language = getattr(request, 'language', '') or ''

        context = create_initial_context(
            title=_title_for_request(task, request),
            language=language,
            prompt_version=DEFAULT_PROMPT_VERSION,
            task=str(task),
        )
        context.extension_data['generation'] = {
            'task': task,
            'request': request,
            'provider_name': provider_name,
            'method_name': method_name,
        }

        started_at = utc_now()
        started_perf = time.perf_counter()
        try:
            context = self.workflow.execute(context)
        except StageExecutionError as exc:
            finished_at = utc_now()
            duration_ms = round((time.perf_counter() - started_perf) * 1000, 3)
            prompt_length = int(context.extension_data.get('prompt_length') or 0)
            cause = exc.__cause__
            if isinstance(cause, GenerationError):
                telemetry = merge_telemetry(
                    getattr(cause, 'telemetry', None),
                    provider=context.provider or '',
                    started_at=started_at,
                    finished_at=finished_at,
                    duration_ms=duration_ms,
                    success=False,
                    error_type=type(cause).__name__,
                    prompt_length=prompt_length,
                )
                raise GenerationError(str(cause), telemetry=telemetry) from cause
            if isinstance(cause, ProviderError):
                raise cause from exc
            telemetry = AIExecutionTelemetry(
                provider=context.provider or '',
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                success=False,
                error_type=type(cause or exc).__name__,
                prompt_length=prompt_length,
            )
            raise GenerationError(
                f'Generation failed: {exc}',
                telemetry=telemetry,
            ) from exc

        finished_at = utc_now()
        duration_ms = round((time.perf_counter() - started_perf) * 1000, 3)
        result = context.extension_data.get('generation_result')
        if result is None:
            raise GenerationError(
                'Workflow completed without a generation result.'
            )

        prompt_length = int(context.extension_data.get('prompt_length') or 0)
        content = '' if result.content is None else str(result.content)
        telemetry = merge_telemetry(
            result.telemetry,
            provider=result.provider or context.provider,
            started_at=started_at,
            finished_at=finished_at,
            duration_ms=duration_ms,
            success=result.success,
            error_type=None,
            prompt_length=(
                result.telemetry.prompt_length
                if result.telemetry and result.telemetry.prompt_length
                else prompt_length
            ),
            response_length=(
                result.telemetry.response_length
                if result.telemetry and result.telemetry.response_length
                else len(content)
            ),
        )
        metadata = dict(result.metadata or {})
        metadata.setdefault('prompt_task', str(task))
        prompt_version = context.prompt_version or DEFAULT_PROMPT_VERSION
        if prompt_version:
            metadata.setdefault('prompt_version', prompt_version)
        metadata.setdefault('workflow_state', context.state.value)
        context.extension_data.setdefault('hooks', {})
        context.extension_data['hooks']['completion'] = 'completed'

        result = GenerationResult(
            success=result.success,
            content=result.content,
            metadata=metadata,
            warnings=list(result.warnings or []),
            provider=result.provider,
            telemetry=None,
        )
        return attach_telemetry(result, telemetry)
