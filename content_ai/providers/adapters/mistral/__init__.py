"""Mistral provider adapter (stub — not implemented)."""

from content_ai.providers.exceptions import ProviderUnavailableError


class MistralProvider:
    name = 'mistral'

    def __init__(self, *args, **kwargs):
        raise ProviderUnavailableError(
            'MistralProvider is a stub; not implemented in RFC-005.'
        )
