"""Provider factory — create providers from configuration (RFC-005)."""

from __future__ import annotations

from django.conf import settings

from content_ai.providers.base import BaseAIProvider
from content_ai.providers.exceptions import (
    ConfigurationError,
    ProviderConfigurationError,
    ProviderNotFound,
)
from content_ai.providers.registry import get_registry


class ProviderFactory:
    """
    Create provider instances from configuration.

    Future: feature flags, priorities, fallbacks (not implemented here).
    """

    def __init__(self, registry=None):
        self.registry = registry or get_registry()

    def create(
        self,
        name: str | None = None,
        *,
        require_credentials: bool = False,
    ) -> BaseAIProvider:
        resolved = name if name is not None else getattr(
            settings,
            'CONTENT_AI_PROVIDER',
            None,
        )
        if not resolved:
            raise ConfigurationError('CONTENT_AI_PROVIDER is not configured.')
        try:
            provider_cls = self.registry.get_class(resolved)
        except ProviderNotFound:
            raise
        provider = provider_cls()
        if require_credentials:
            self._validate_credentials(provider)
        return provider

    def _validate_credentials(self, provider: BaseAIProvider) -> None:
        # OpenAI validates in __init__; other adapters may expose api_key.
        api_key = getattr(provider, 'api_key', None)
        if api_key is not None and api_key == '':
            raise ProviderConfigurationError(
                f"Provider '{provider.name}' is missing credentials."
            )
