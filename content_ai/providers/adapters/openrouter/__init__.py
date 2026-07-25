"""OpenRouter provider adapter (stub — not implemented)."""

from content_ai.providers.exceptions import ProviderUnavailableError


class OpenRouterProvider:
    name = 'openrouter'

    def __init__(self, *args, **kwargs):
        raise ProviderUnavailableError(
            'OpenRouterProvider is a stub; not implemented in RFC-005.'
        )
