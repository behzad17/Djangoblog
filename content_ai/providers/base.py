"""Abstract AI provider interface.

Concrete vendors must subclass ``BaseAIProvider``. Application code depends
only on this interface, never on a specific vendor SDK.

RFC-005 extends the contract with optional platform methods (health, capabilities,
usage). Existing generate_* methods remain the production generation API.
"""

from __future__ import annotations

from content_ai.providers.capabilities import ProviderCapabilities
from content_ai.providers.models import ModelMetadata, UsageReport


class BaseAIProvider:
    """
    Contract for Content AI providers.

    Methods accept a plain prompt string (built by the prompt layer) and must
    return ``GenerationResult``. Base generate methods raise
    ``NotImplementedError``. No network I/O belongs in this base class.
    """

    name = 'base'

    def generate_post(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement generate_post()'
        )

    def generate_ad(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement generate_ad()'
        )

    def rewrite(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement rewrite()'
        )

    def summarize(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement summarize()'
        )

    def translate(self, prompt=''):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement translate()'
        )

    def generate_image(self, prompt='', *, aspect_ratio='16:9', **kwargs):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement generate_image()'
        )

    # --- RFC-005 platform surface (optional; safe defaults) ---

    def generate(self, prompt='', *, task='post_generation'):
        """
        Generic generate entry. Defaults to ``generate_post``.

        Adapters may override for task routing without changing callers.
        """
        if task == 'ad_generation':
            return self.generate_ad(prompt)
        if task == 'rewrite':
            return self.rewrite(prompt)
        if task == 'summary':
            return self.summarize(prompt)
        if task == 'translation':
            return self.translate(prompt)
        return self.generate_post(prompt)

    def stream(self, prompt='', **kwargs):
        raise NotImplementedError(
            f'{type(self).__name__} does not implement stream()'
        )

    def health_check(self) -> bool:
        """Return True when the provider appears healthy (default: True)."""
        return True

    def capabilities(self) -> ProviderCapabilities:
        """Declare provider capabilities (override in adapters)."""
        return ProviderCapabilities(text_generation=True)

    def discover_models(self) -> list[ModelMetadata]:
        """Return known models for this provider (default: empty)."""
        return []

    def estimate_cost(
        self,
        *,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        model: str = '',
    ) -> float | None:
        """Estimate cost in currency units if known (default: None)."""
        return None

    def last_usage(self) -> UsageReport | None:
        """Return the most recent usage report if the adapter tracks one."""
        return None
