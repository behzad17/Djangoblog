"""Single orchestration entry point for Content AI generation."""

from content_ai.constants import AIGenerationTask
from content_ai.prompts.registry import get_prompt_template
from content_ai.providers.exceptions import GenerationError
from content_ai.providers.registry import get_provider

# Maps generation tasks to BaseAIProvider method names.
_TASK_METHODS = {
    AIGenerationTask.POST_GENERATION: 'generate_post',
    AIGenerationTask.AD_GENERATION: 'generate_ad',
    AIGenerationTask.REWRITE: 'rewrite',
    AIGenerationTask.SUMMARY: 'summarize',
    AIGenerationTask.TRANSLATION: 'translate',
}


class ContentGenerationService:
    """
    Orchestrates AI generation via prompt templates and the configured provider.

    Flow: request → prompt template → prompt string → provider → GenerationResult.
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

        template = get_prompt_template(task)
        prompt = template.build(request)

        provider = get_provider(provider_name or None)
        method = getattr(provider, method_name, None)
        if method is None:
            raise GenerationError(
                f"Provider '{provider.name}' does not support task '{task}'."
            )

        return method(prompt)
