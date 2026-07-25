"""Placeholder prompt template for blog-post generation."""

from content_ai.prompts.base import BasePromptTemplate
from content_ai.schemas.requests import PostGenerationRequest


class PostPromptTemplate(BasePromptTemplate):
    """Deterministic placeholder prompt for ``POST_GENERATION``."""

    def build(self, request=None) -> str:
        req = request if request is not None else PostGenerationRequest()
        return (
            'System: You are a Peyvand content assistant.\n'
            'Task: POST_GENERATION\n'
            f'Title: {req.title}\n'
            f'Source: {req.source}\n'
            f'Language: {req.language}\n'
            f'Category: {req.category}\n'
            f'Context: {req.context}\n'
            f'Instructions: {req.instructions}\n'
        )
