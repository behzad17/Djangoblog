"""Prompt template for advertisement generation (markdown asset-backed)."""

from content_ai.prompts.base import AssetPromptTemplate
from content_ai.schemas.requests import AdGenerationRequest


class AdPromptTemplate(AssetPromptTemplate):
    """Loads ``prompts/ads/{version}.md`` and injects request fields."""

    kind = 'ads'
    request_class = AdGenerationRequest

    def _values(self, request) -> dict:
        req = request if isinstance(request, AdGenerationRequest) else (
            AdGenerationRequest()
        )
        return {
            'business_name': req.business_name,
            'category': req.category,
            'language': req.language,
            'city': req.city,
            'description': req.description,
            'target_audience': req.target_audience,
            'instructions': req.instructions,
        }
