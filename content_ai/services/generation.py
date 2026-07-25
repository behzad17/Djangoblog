"""Single orchestration entry point for Content AI generation."""

from content_ai.constants import AIGenerationTask
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
    Orchestrates AI generation via the configured provider.

    Resolves the provider, delegates by task, and returns the provider result.
    No validation, persistence, or business logic.
    """

    def generate(self, task, payload=None):
        """
        Run ``task`` against the configured provider.

        ``payload`` should be a mapping of keyword arguments for the provider
        method. Defaults to an empty mapping.
        """
        method_name = _TASK_METHODS.get(task)
        if method_name is None:
            raise GenerationError(f"Unsupported generation task: '{task}'.")

        provider = get_provider()
        method = getattr(provider, method_name, None)
        if method is None:
            raise GenerationError(
                f"Provider '{provider.name}' does not support task '{task}'."
            )

        kwargs = {} if payload is None else dict(payload)
        return method(**kwargs)
