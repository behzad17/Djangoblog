"""Deterministic mock provider for architecture and tests. No network calls."""

from content_ai.providers.base import BaseAIProvider

MOCK_RESPONSE = 'Mock AI response'


class MockProvider(BaseAIProvider):
    """
    Fake provider used only to exercise the provider interface.

    Returns deterministic payloads. Never performs HTTP or SDK calls.
    """

    name = 'mock'

    def generate_post(self, *args, **kwargs):
        return {
            'title': MOCK_RESPONSE,
            'content': MOCK_RESPONSE,
            'excerpt': MOCK_RESPONSE,
        }

    def generate_ad(self, *args, **kwargs):
        return {
            'title': MOCK_RESPONSE,
            'description': MOCK_RESPONSE,
        }

    def rewrite(self, *args, **kwargs):
        return {'text': MOCK_RESPONSE}

    def summarize(self, *args, **kwargs):
        return {'summary': MOCK_RESPONSE}

    def translate(self, *args, **kwargs):
        return {'text': MOCK_RESPONSE}
