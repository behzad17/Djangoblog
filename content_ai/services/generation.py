"""Single orchestration entry point for Content AI generation."""

import time

from content_ai.config import DEFAULT_PROMPT_VERSION, DEFAULT_STYLE
from content_ai.constants import AIGenerationTask
from content_ai.prompts.builders import PromptBuilder
from content_ai.prompts.registry import get_prompt_template
from content_ai.providers.exceptions import GenerationError
from content_ai.providers.registry import get_provider
from content_ai.schemas.responses import GenerationResult
from content_ai.telemetry import (
    AIExecutionTelemetry,
    attach_telemetry,
    merge_telemetry,
    utc_now,
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


class ContentGenerationService:
    """
    Orchestrates AI generation via PromptBuilder and the configured provider.

    Flow: request → task user prompt → PromptBuilder → provider → GenerationResult.
    Measures execution timing and attaches ``AIExecutionTelemetry``.
    No validation, persistence, or business logic.
    """

    def generate(self, task, request=None, provider_name=None):
        """
        Run ``task`` against the configured provider.

        ``request`` should be a canonical request schema (e.g.
        ``PostGenerationRequest`` / ``AdGenerationRequest``) when applicable.
        ``provider_name`` optionally overrides ``settings.CONTENT_AI_PROVIDER``.
        """
        method_name = _TASK_METHODS.get(task)
        if method_name is None:
            raise GenerationError(f"Unsupported generation task: '{task}'.")

        prompt, prompt_version = build_generation_prompt(task, request)
        prompt_length = len(prompt or '')

        provider = get_provider(provider_name or None)
        method = getattr(provider, method_name, None)
        if method is None:
            raise GenerationError(
                f"Provider '{provider.name}' does not support task '{task}'."
            )

        started_at = utc_now()
        started_perf = time.perf_counter()
        try:
            result = method(prompt)
        except GenerationError as exc:
            finished_at = utc_now()
            duration_ms = round((time.perf_counter() - started_perf) * 1000, 3)
            telemetry = merge_telemetry(
                getattr(exc, 'telemetry', None),
                provider=provider.name,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                success=False,
                error_type=type(exc).__name__,
                prompt_length=prompt_length,
            )
            raise GenerationError(str(exc), telemetry=telemetry) from exc
        except Exception as exc:
            finished_at = utc_now()
            duration_ms = round((time.perf_counter() - started_perf) * 1000, 3)
            telemetry = AIExecutionTelemetry(
                provider=provider.name,
                started_at=started_at,
                finished_at=finished_at,
                duration_ms=duration_ms,
                success=False,
                error_type=type(exc).__name__,
                prompt_length=prompt_length,
            )
            raise GenerationError(
                f'Generation failed: {exc}',
                telemetry=telemetry,
            ) from exc

        finished_at = utc_now()
        duration_ms = round((time.perf_counter() - started_perf) * 1000, 3)
        content = '' if result.content is None else str(result.content)
        telemetry = merge_telemetry(
            result.telemetry,
            provider=result.provider or provider.name,
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
        if prompt_version:
            metadata.setdefault('prompt_version', prompt_version)
        result = GenerationResult(
            success=result.success,
            content=result.content,
            metadata=metadata,
            warnings=list(result.warnings or []),
            provider=result.provider,
            telemetry=None,
        )
        return attach_telemetry(result, telemetry)
