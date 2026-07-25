"""Provider registry / factory for Content AI (RFC-005 compatible).

Existing ``get_provider`` / ``list_providers`` remain the production API.
``ProviderRegistry`` adds explicit registration/discovery for the platform.
"""

from __future__ import annotations

from django.conf import settings

from content_ai.providers.base import BaseAIProvider
from content_ai.providers.exceptions import (
    ProviderConfigurationError,
    ProviderNotFound,
)
from content_ai.providers.mock import MockProvider
from content_ai.providers.openai import OpenAIProvider

# Shared production registry map (default ProviderRegistry uses this dict).
_PROVIDERS: dict[str, type[BaseAIProvider]] = {
    'mock': MockProvider,
    'openai': OpenAIProvider,
}


class ProviderRegistry:
    """
    Register and discover provider classes.

    The default registry shares the production ``_PROVIDERS`` map so
    ``get_provider`` stays compatible. Isolated instances use a private copy.
    """

    def __init__(self, initial: dict[str, type[BaseAIProvider]] | None = None):
        if initial is None:
            self._providers = _PROVIDERS
        else:
            self._providers = dict(initial)

    def register(self, name: str, provider_cls: type[BaseAIProvider]) -> None:
        key = (name or '').strip()
        if not key:
            raise ProviderConfigurationError('Provider name is required.')
        if not isinstance(provider_cls, type) or not issubclass(
            provider_cls, BaseAIProvider
        ):
            raise ProviderConfigurationError(
                'provider_cls must be a BaseAIProvider subclass.'
            )
        if key in self._providers:
            raise ProviderConfigurationError(
                f'Duplicate provider registration: {key!r}.'
            )
        self._providers[key] = provider_cls

    def get_class(self, name: str) -> type[BaseAIProvider]:
        try:
            return self._providers[name]
        except KeyError as exc:
            raise ProviderNotFound(
                f"Unknown Content AI provider: '{name}'."
            ) from exc

    def list_providers(self) -> list[str]:
        return sorted(self._providers.keys())

    def available(self) -> dict[str, type[BaseAIProvider]]:
        return dict(self._providers)


_DEFAULT_REGISTRY = ProviderRegistry()


def get_registry() -> ProviderRegistry:
    return _DEFAULT_REGISTRY


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
    provider_cls = get_registry().get_class(resolved)
    return provider_cls()


def list_providers():
    """Return the registered provider names."""
    return get_registry().list_providers()


def register_provider(name: str, provider_cls: type[BaseAIProvider]) -> None:
    """Register a provider class on the default registry."""
    get_registry().register(name, provider_cls)
