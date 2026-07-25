"""Prompt template registry for Content AI."""

from content_ai.constants import AIGenerationTask
from content_ai.prompts.ads import AdPromptTemplate
from content_ai.prompts.base import BasePromptTemplate
from content_ai.prompts.post import PostPromptTemplate
from content_ai.providers.exceptions import GenerationError

_PROMPT_TEMPLATES = {
    AIGenerationTask.POST_GENERATION: PostPromptTemplate,
    AIGenerationTask.AD_GENERATION: AdPromptTemplate,
}


def get_prompt_template(task, version=None) -> BasePromptTemplate:
    """
    Resolve a prompt template for ``task``.

    Optional ``version`` selects a Git-managed markdown asset (default ``v1``).
    Unknown or unregistered tasks raise ``GenerationError``.
    """
    template_cls = _PROMPT_TEMPLATES.get(task)
    if template_cls is None:
        raise GenerationError(
            f"No prompt template registered for task: '{task}'."
        )
    if version is None:
        return template_cls()
    return template_cls(version=version)


def list_prompt_tasks():
    """Return task values that have a registered prompt template."""
    return sorted(_PROMPT_TEMPLATES.keys())
