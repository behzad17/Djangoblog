"""OpenAI provider using the Responses API.

Never exposes raw SDK response objects to callers.
"""

from __future__ import annotations

import logging
import time

from django.conf import settings

from content_ai.providers.base import BaseAIProvider
from content_ai.providers.capabilities import ProviderCapabilities
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
)
from content_ai.providers.models import ModelMetadata
from content_ai.schemas.responses import GenerationResult
from content_ai.telemetry import AIExecutionTelemetry

logger = logging.getLogger(__name__)

# DALL·E 3 landscape size closest to 16:9 hero images.
_DEFAULT_IMAGE_SIZE = '1792x1024'
_DEFAULT_IMAGE_MODEL = 'dall-e-3'


def _aspect_to_openai_size(aspect_ratio: str | None) -> str:
    ratio = (aspect_ratio or '16:9').strip()
    if ratio in ('1:1', 'square'):
        return '1024x1024'
    if ratio in ('9:16', 'portrait'):
        return '1024x1792'
    return _DEFAULT_IMAGE_SIZE


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


def _openai_error_details(exc):
    """
    Collect OpenAI / httpx exception fields for diagnostics.

    Prefer structured ``body`` / ``error.code`` / ``error.message`` when present.
    """
    details = {
        'exception_type': type(exc).__name__,
        'message': str(exc),
    }
    status_code = getattr(exc, 'status_code', None)
    if status_code is not None:
        details['status_code'] = status_code

    body = getattr(exc, 'body', None)
    if body is not None:
        details['body'] = body
        error_obj = None
        if isinstance(body, dict):
            nested = body.get('error')
            error_obj = nested if isinstance(nested, dict) else body
        if isinstance(error_obj, dict):
            if error_obj.get('code') is not None:
                details['error_code'] = error_obj.get('code')
            if error_obj.get('message') is not None:
                details['error_message'] = error_obj.get('message')
            if error_obj.get('type') is not None:
                details['error_type'] = error_obj.get('type')
            if error_obj.get('param') is not None:
                details['error_param'] = error_obj.get('param')

    code = getattr(exc, 'code', None)
    if code is not None and 'error_code' not in details:
        details['error_code'] = code

    request_id = getattr(exc, 'request_id', None)
    if request_id:
        details['request_id'] = request_id

    response = getattr(exc, 'response', None)
    if response is not None:
        text = getattr(response, 'text', None)
        if text:
            details['response_text'] = text
        if status_code is None:
            response_status = getattr(response, 'status_code', None)
            if response_status is not None:
                details['status_code'] = response_status

    return details


class OpenAIProvider(BaseAIProvider):
    """
    Real OpenAI provider backed by ``client.responses.create``.

    Requires ``OPENAI_API_KEY`` and ``OPENAI_MODEL`` in Django settings.
    """

    name = 'openai'

    def __init__(self, client=None):
        self.api_key = getattr(settings, 'OPENAI_API_KEY', '') or ''
        self.model = getattr(settings, 'OPENAI_MODEL', '') or ''
        self.image_model = (
            getattr(settings, 'OPENAI_IMAGE_MODEL', '') or _DEFAULT_IMAGE_MODEL
        )
        self.image_size = (
            getattr(settings, 'OPENAI_IMAGE_SIZE', '') or _DEFAULT_IMAGE_SIZE
        )
        # Short timeout avoids Heroku H12 (~30s); no retries so errors surface fast.
        self.timeout = 20

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
                timeout=20,
                max_retries=0,
            )

    def generate_post(self, prompt=''):
        return self._generate(prompt, task='post_generation')

    def generate_ad(self, prompt=''):
        return self._generate(prompt, task='ad_generation')

    def capabilities(self) -> ProviderCapabilities:
        return ProviderCapabilities(
            text_generation=True,
            json_output=False,
            streaming=False,
            structured_output=False,
            long_context=True,
            image_generation=True,
        )

    def generate_image(self, prompt='', *, aspect_ratio='16:9', **kwargs):
        from content_ai.providers.models import ImageGenerationResult

        prompt_text = (prompt or '').strip()
        if not prompt_text:
            raise GenerationError('Image prompt is required.')

        size = kwargs.get('size') or _aspect_to_openai_size(aspect_ratio)
        if not size:
            size = self.image_size or _DEFAULT_IMAGE_SIZE
        model = kwargs.get('model') or self.image_model or _DEFAULT_IMAGE_MODEL

        logger.info(
            'OpenAI image request starting: model=%s size=%s prompt_chars=%d',
            model,
            size,
            len(prompt_text),
        )
        started = time.monotonic()
        try:
            response = self._client.images.generate(
                model=model,
                prompt=prompt_text,
                size=size,
                quality=kwargs.get('quality') or 'standard',
                n=1,
            )
        except Exception as exc:
            elapsed = time.monotonic() - started
            details = _openai_error_details(exc)
            logger.exception(
                'OpenAI image generation failed after %.2fs: details=%s',
                elapsed,
                details,
            )
            raise GenerationError(
                f'OpenAI image generation failed: {exc}'
            ) from exc

        elapsed = time.monotonic() - started
        data = list(getattr(response, 'data', None) or [])
        if not data:
            raise GenerationError('OpenAI image generation returned no images.')
        first = data[0]
        image_url = getattr(first, 'url', None) or ''
        b64 = getattr(first, 'b64_json', None) or ''
        b64_data_url = f'data:image/png;base64,{b64}' if b64 else ''
        revised = getattr(first, 'revised_prompt', None) or ''
        if not image_url and not b64_data_url:
            raise GenerationError('OpenAI image generation returned empty payload.')

        logger.info(
            'OpenAI image response received: model=%s elapsed=%.2fs',
            model,
            elapsed,
        )
        return ImageGenerationResult(
            success=True,
            image_url=image_url or b64_data_url,
            b64_data_url=b64_data_url,
            revised_prompt=str(revised),
            provider=self.name,
            model=model,
            metadata={
                'size': size,
                'aspect_ratio': aspect_ratio or '16:9',
                'duration_ms': round(elapsed * 1000, 3),
            },
        )

    def discover_models(self) -> list[ModelMetadata]:
        return [
            ModelMetadata(
                provider=self.name,
                model=self.model,
                supports_json=False,
                supports_streaming=False,
                status='available',
            )
        ]

    def _generate(self, prompt, task):
        prompt_text = prompt or ''
        logger.info(
            'OpenAI request starting: model=%s timeout=%s prompt_chars=%d preview=%r',
            self.model,
            self.timeout,
            len(prompt_text),
            prompt_text[:300],
        )
        started = time.monotonic()
        try:
            response = self._client.responses.create(
                model=self.model,
                input=prompt,
            )
        except Exception as exc:
            elapsed = time.monotonic() - started
            details = _openai_error_details(exc)
            logger.exception(
                'OpenAI generation failed after %.2fs: '
                'exception_type=%s message=%s status_code=%s error_code=%s '
                'error_message=%s request_id=%s body=%s response_text=%s details=%s',
                elapsed,
                details.get('exception_type'),
                details.get('message'),
                details.get('status_code'),
                details.get('error_code'),
                details.get('error_message'),
                details.get('request_id'),
                details.get('body'),
                details.get('response_text'),
                details,
            )
            telemetry = AIExecutionTelemetry(
                provider=self.name,
                model=self.model,
                success=False,
                error_type=type(exc).__name__,
                prompt_length=len(prompt_text),
                response_length=0,
                duration_ms=round(elapsed * 1000, 3),
                metadata={
                    'openai_status_code': details.get('status_code'),
                    'openai_error_code': details.get('error_code'),
                    'openai_error_message': details.get('error_message'),
                    'openai_request_id': details.get('request_id'),
                },
            )
            raise GenerationError(
                f'OpenAI generation failed: {exc}',
                telemetry=telemetry,
            ) from exc

        elapsed = time.monotonic() - started
        logger.info(
            'OpenAI response received successfully: model=%s elapsed=%.2fs',
            self.model,
            elapsed,
        )

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
            duration_ms=round(elapsed * 1000, 3),
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
