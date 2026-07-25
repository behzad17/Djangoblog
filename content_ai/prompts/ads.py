"""Placeholder prompt template for advertisement generation."""

from content_ai.prompts.base import BasePromptTemplate
from content_ai.schemas.requests import AdGenerationRequest


class AdPromptTemplate(BasePromptTemplate):
    """Deterministic placeholder prompt for ``AD_GENERATION``."""

    def build(self, request=None) -> str:
        req = request if request is not None else AdGenerationRequest()
        return (
            'System: You are a Peyvand advertising assistant.\n'
            'Task: AD_GENERATION\n'
            f'Business name: {req.business_name}\n'
            f'Category: {req.category}\n'
            f'Language: {req.language}\n'
            f'City: {req.city}\n'
            f'Description: {req.description}\n'
            f'Target audience: {req.target_audience}\n'
            f'Instructions: {req.instructions}\n'
        )
