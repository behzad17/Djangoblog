"""Provider registry / factory for Content AI."""

from django.conf import settings

from content_ai.providers.base import BaseAIProvider
from content_ai.providers.exceptions import (
    ProviderConfigurationError,
    ProviderNotFound,
)
from content_ai.providers.mock import MockProvider
from content_ai.providers.openai import OpenAIProvider

_PROVIDERS = {
    'mock': MockProvider,
    'openai': OpenAIProvider,
}


def get_provider(name=None) -> BaseAIProvider:
    """
    Resolve a provider by name.

    If ``name`` is omitted, uses ``settings.CONTENT_AI_PROVIDER``.
    Unknown names raise ``ProviderNotFound``.
    """
    resolved = name if name is not None else getattr(
        settings,
        'CONTENT_AI_PROVIDER',
        None,
    )
    if not resolved:
        raise ProviderConfigurationError(
            'CONTENT_AI_PROVIDER is not configured.'
        )

    provider_cls = _PROVIDERS.get(resolved)
    if provider_cls is None:
        raise ProviderNotFound(
            f"Unknown Content AI provider: '{resolved}'."
        )
    return provider_cls()


def list_providers():
    """Return the registered provider names."""
    return sorted(_PROVIDERS.keys())
