"""Gemini provider adapter (stub — not implemented)."""

from content_ai.providers.exceptions import ProviderUnavailableError


class GeminiProvider:
    name = 'gemini'

    def __init__(self, *args, **kwargs):
        raise ProviderUnavailableError(
            'GeminiProvider is a stub; not implemented in RFC-005.'
        )
