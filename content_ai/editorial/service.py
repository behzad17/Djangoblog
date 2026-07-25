"""Editorial domain service for in-memory AI draft generation."""

from __future__ import annotations

from content_ai.constants import AIGenerationTask
from content_ai.editorial.drafts import EditorialDraft
from content_ai.schemas.requests import PostGenerationRequest
from content_ai.schemas.responses import GenerationResult
from content_ai.services.generation import ContentGenerationService


class EditorialAIService:
    """
    Domain orchestration for editorial content generation.

    Creates a ``PostGenerationRequest``, runs the generation pipeline, and
    maps ``GenerationResult`` to an in-memory ``EditorialDraft``.
    Does not persist, parse Markdown, create slugs, or assign authors.
    """

    def __init__(self, generation_service=None):
        self._generation_service = (
            generation_service or ContentGenerationService()
        )

    def generate_draft(
        self,
        *,
        title='',
        source='',
        language='',
        category='',
        context='',
        instructions='',
        provider_name=None,
    ) -> EditorialDraft:
        request = PostGenerationRequest(
            title=title,
            source=source,
            language=language,
            category=category,
            context=context,
            instructions=instructions,
        )
        result = self._generation_service.generate(
            AIGenerationTask.POST_GENERATION,
            request,
            provider_name=provider_name,
        )
        return self._to_draft(request, result)

    def _to_draft(
        self,
        request: PostGenerationRequest,
        result: GenerationResult,
    ) -> EditorialDraft:
        body = '' if result.content is None else str(result.content)
        metadata = dict(result.metadata)
        metadata.setdefault('provider', result.provider)
        metadata.setdefault('success', result.success)
        metadata.setdefault('warnings', list(result.warnings))
        return EditorialDraft(
            title=request.title,
            body=body,
            summary='',
            language=request.language,
            metadata=metadata,
        )
