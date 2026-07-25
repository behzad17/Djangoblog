"""Deterministic mock provider for architecture and tests. No network calls."""

from content_ai.providers.base import BaseAIProvider
from content_ai.schemas.responses import GenerationResult

MOCK_RESPONSE = 'Mock AI response'


class MockProvider(BaseAIProvider):
    """
    Fake provider used only to exercise the provider interface.

    Accepts a prompt string and returns deterministic ``GenerationResult``
    values. Never performs HTTP or SDK calls.
    """

    name = 'mock'

    def _result(self, prompt='', metadata=None, warnings=None):
        meta = {'prompt': prompt}
        if metadata:
            meta.update(metadata)
        return GenerationResult(
            success=True,
            content=MOCK_RESPONSE,
            metadata=meta,
            warnings=[] if warnings is None else warnings,
            provider=self.name,
        )

    def generate_post(self, prompt=''):
        return self._result(prompt=prompt, metadata={'task': 'post_generation'})

    def generate_ad(self, prompt=''):
        return self._result(prompt=prompt, metadata={'task': 'ad_generation'})

    def rewrite(self, prompt=''):
        return self._result(prompt=prompt, metadata={'task': 'rewrite'})

    def summarize(self, prompt=''):
        return self._result(prompt=prompt, metadata={'task': 'summary'})

    def translate(self, prompt=''):
        return self._result(prompt=prompt, metadata={'task': 'translation'})
