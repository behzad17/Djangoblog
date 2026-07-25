"""Deterministic mock provider for architecture and tests. No network calls."""

from content_ai.providers.base import BaseAIProvider
from content_ai.schemas.responses import GenerationResult
from content_ai.telemetry import AIExecutionTelemetry

MOCK_RESPONSE = 'Mock AI response'
MOCK_MODEL = 'mock'


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
        prompt_text = prompt or ''
        telemetry = AIExecutionTelemetry(
            provider=self.name,
            model=MOCK_MODEL,
            success=True,
            prompt_length=len(prompt_text),
            response_length=len(MOCK_RESPONSE),
            token_usage=None,
            estimated_cost=None,
            metadata={'source': 'mock'},
        )
        return GenerationResult(
            success=True,
            content=MOCK_RESPONSE,
            metadata=meta,
            warnings=[] if warnings is None else warnings,
            provider=self.name,
            telemetry=telemetry,
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
