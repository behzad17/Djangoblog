"""Claude provider adapter (stub — not implemented)."""

from content_ai.providers.exceptions import ProviderUnavailableError


class ClaudeProvider:
    name = 'claude'

    def __init__(self, *args, **kwargs):
        raise ProviderUnavailableError(
            'ClaudeProvider is a stub; not implemented in RFC-005.'
        )
