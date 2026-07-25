"""Local / self-hosted provider adapter (stub — not implemented)."""

from content_ai.providers.exceptions import ProviderUnavailableError


class LocalProvider:
    name = 'local'

    def __init__(self, *args, **kwargs):
        raise ProviderUnavailableError(
            'LocalProvider is a stub; not implemented in RFC-005.'
        )
