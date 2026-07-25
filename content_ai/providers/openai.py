"""OpenAI provider using the Responses API.

Never exposes raw SDK response objects to callers.
"""

from __future__ import annotations

from django.conf import settings

from content_ai.providers.base import BaseAIProvider
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
)
from content_ai.schemas.responses import GenerationResult
from content_ai.telemetry import AIExecutionTelemetry


def _extract_token_usage(response):
    """Map SDK usage fields into a plain dict. Never return the SDK object."""
    usage = getattr(response, 'usage', None)
    if usage is None:
        return None
    return {
        'input_tokens': getattr(usage, 'input_tokens', None),
        'output_tokens': getattr(usage, 'output_tokens', None),
        'total_tokens': getattr(usage, 'total_tokens', None),
    }


class OpenAIProvider(BaseAIProvider):
    """
    Real OpenAI provider backed by ``client.responses.create``.

    Requires ``OPENAI_API_KEY`` and ``OPENAI_MODEL`` in Django settings.
    """

    name = 'openai'

    def __init__(self, client=None):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', '') or ''
        self.model = getattr(settings, 'OPENAI_MODEL', '') or ''
        self.timeout = getattr(settings, 'OPENAI_TIMEOUT', 60)

        if not self.api_key:
            raise ProviderConfigurationError(
                'OPENAI_API_KEY is not configured.'
            )
        if not self.model:
            raise ProviderConfigurationError(
                'OPENAI_MODEL is not configured.'
            )

        if client is not None:
            self._client = client
        else:
            from openai import OpenAI

            self._client = OpenAI(
                api_key=self.api_key,
                timeout=self.timeout,
            )

    def generate_post(self, prompt=''):
        return self._generate(prompt, task='post_generation')

    def generate_ad(self, prompt=''):
        return self._generate(prompt, task='ad_generation')

    def _generate(self, prompt, task):
        prompt_text = prompt or ''
        try:
            response = self._client.responses.create(
                model=self.model,
                input=prompt,
            )
        except Exception as exc:
            telemetry = AIExecutionTelemetry(
                provider=self.name,
                model=self.model,
                success=False,
                error_type=type(exc).__name__,
                prompt_length=len(prompt_text),
                response_length=0,
            )
            raise GenerationError(
                f'OpenAI generation failed: {exc}',
                telemetry=telemetry,
            ) from exc

        content = getattr(response, 'output_text', None)
        if content is None:
            content = ''
        content_text = str(content)

        telemetry = AIExecutionTelemetry(
            provider=self.name,
            model=self.model,
            success=True,
            prompt_length=len(prompt_text),
            response_length=len(content_text),
            token_usage=_extract_token_usage(response),
            estimated_cost=None,
            metadata={'response_id': getattr(response, 'id', None)},
        )
        return GenerationResult(
            success=True,
            content=content,
            metadata={
                'task': task,
                'model': self.model,
                'response_id': getattr(response, 'id', None),
            },
            provider=self.name,
            telemetry=telemetry,
        )
