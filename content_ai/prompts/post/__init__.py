"""Prompt template for blog-post generation (markdown asset-backed)."""

from content_ai.prompts.base import AssetPromptTemplate
from content_ai.schemas.requests import PostGenerationRequest


class PostPromptTemplate(AssetPromptTemplate):
    """Loads ``prompts/post/{version}.md`` and injects request fields."""

    kind = 'post'
    request_class = PostGenerationRequest

    def _values(self, request) -> dict:
        req = request if isinstance(request, PostGenerationRequest) else (
            PostGenerationRequest()
        )
        return {
            'title': req.title,
            'source': req.source,
            'language': req.language,
            'category': req.category,
            'context': req.context,
            'instructions': req.instructions,
        }
