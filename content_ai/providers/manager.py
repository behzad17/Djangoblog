"""Provider manager — selection, logging, and policy hooks (RFC-005)."""

from __future__ import annotations

import logging
import time
from typing import Any

from content_ai.providers.base import BaseAIProvider
from content_ai.providers.capabilities import ProviderCapabilities
from content_ai.providers.exceptions import (
    CapabilityError,
    ProviderError,
    ProviderUnavailableError,
)
from content_ai.providers.factory import ProviderFactory
from content_ai.providers.models import UsageReport, utc_now

logger = logging.getLogger(__name__)


class ProviderManager:
    """
    Select and invoke providers without leaking vendor-specific logic.

    Retries / circuit breakers / failover are hooks only — not implemented.
    """

    def __init__(
        self,
        factory: ProviderFactory | None = None,
        *,
        default_provider: str | None = None,
        max_retries: int = 0,
        timeout_seconds: float | None = None,
    ):
        self.factory = factory or ProviderFactory()
        self.default_provider = default_provider
        self.max_retries = max(0, int(max_retries))
        self.timeout_seconds = timeout_seconds
        self._last_usage: UsageReport | None = None
        # Future: circuit breaker state, fallback chain, selection policy.
        self.extension_hooks: dict[str, Any] = {
            'circuit_breaker': 'pending',
            'failover': 'pending',
            'load_balancing': 'pending',
            'automatic_selection': 'pending',
        }

    def select_provider(self, name: str | None = None) -> BaseAIProvider:
        provider = self.factory.create(name or self.default_provider)
        if not provider.health_check():
            raise ProviderUnavailableError(
                f"Provider '{provider.name}' failed health_check()."
            )
        return provider

    def require_capability(
        self,
        provider: BaseAIProvider,
        capability: str,
    ) -> ProviderCapabilities:
        caps = provider.capabilities()
        if not caps.supports(capability):
            raise CapabilityError(
                f"Provider '{provider.name}' lacks capability {capability!r}."
            )
        return caps

    def generate(
        self,
        prompt: str = '',
        *,
        provider_name: str | None = None,
        task: str = 'post_generation',
        require_capability: str | None = None,
    ):
        """
        Run generation via the selected provider.

        Retries are counted but default ``max_retries=0`` preserves fail-fast
        production OpenAI behaviour when callers use OpenAIProvider directly.
        """
        provider = self.select_provider(provider_name)
        if require_capability:
            self.require_capability(provider, require_capability)

        attempts = self.max_retries + 1
        last_error: Exception | None = None
        started = time.perf_counter()
        for attempt in range(attempts):
            try:
                logger.info(
                    'ProviderManager generate: provider=%s task=%s attempt=%s',
                    provider.name,
                    task,
                    attempt + 1,
                )
                result = provider.generate(prompt, task=task)
                latency_ms = round((time.perf_counter() - started) * 1000, 3)
                usage = provider.last_usage()
                if usage is None:
                    usage = UsageReport(
                        provider=provider.name,
                        model=getattr(provider, 'model', '') or '',
                        latency_ms=latency_ms,
                        timestamp=utc_now(),
                    )
                self._last_usage = usage
                return result
            except ProviderError as exc:
                last_error = exc
                logger.warning(
                    'ProviderManager attempt failed: provider=%s error=%s',
                    provider.name,
                    exc,
                )
                if attempt + 1 >= attempts:
                    break
                # Future: backoff / circuit breaker.
        assert last_error is not None
        raise last_error

    def last_usage(self) -> UsageReport | None:
        return self._last_usage
