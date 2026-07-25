"""OpenAI provider using the Responses API.

Never exposes raw SDK response objects to callers.
"""

from __future__ import annotations

import logging

from django.conf import settings

from content_ai.providers.base import BaseAIProvider
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
)
from content_ai.schemas.responses import GenerationResult
from content_ai.telemetry import AIExecutionTelemetry

logger = logging.getLogger(__name__)


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
            details = _openai_error_details(exc)
            # Full stack + OpenAI payload (status, body, error.code/message).
            logger.exception(
                'OpenAI generation failed before GenerationError: '
                'status_code=%s error_code=%s error_message=%s body=%s details=%s',
                details.get('status_code'),
                details.get('error_code'),
                details.get('error_message'),
                details.get('body'),
                details,
            )
            telemetry = AIExecutionTelemetry(
                provider=self.name,
                model=self.model,
                success=False,
                error_type=type(exc).__name__,
                prompt_length=len(prompt_text),
                response_length=0,
                metadata={
                    'openai_status_code': details.get('status_code'),
                    'openai_error_code': details.get('error_code'),
                    'openai_error_message': details.get('error_message'),
                },
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
