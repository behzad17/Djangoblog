"""Lightweight JSON serializers for the internal Content AI API.

No Django REST Framework — keep the surface minimal and dependency-free.
"""

from __future__ import annotations

from content_ai.telemetry import AIExecutionTelemetry

POST_GENERATION_FIELDS = (
    'title',
    'source',
    'language',
    'category',
    'context',
    'instructions',
)


class SerializationError(ValueError):
    """Raised when request JSON cannot be normalized."""


def parse_editorial_draft_request(data):
    """
    Normalize JSON into kwargs for ``EditorialAIService.generate_draft``.

    Accepts fields matching ``PostGenerationRequest`` plus optional
    ``provider_name``.
    """
    if data is None:
        raise SerializationError('Request body is required.')
    if not isinstance(data, dict):
        raise SerializationError('Request body must be a JSON object.')

    unknown = set(data.keys()) - set(POST_GENERATION_FIELDS) - {'provider_name'}
    if unknown:
        raise SerializationError(
            f"Unknown fields: {', '.join(sorted(unknown))}."
        )

    kwargs = {}
    for field in POST_GENERATION_FIELDS:
        value = data.get(field, '')
        if value is None:
            value = ''
        if not isinstance(value, str):
            raise SerializationError(f"Field '{field}' must be a string.")
        kwargs[field] = value

    provider_name = data.get('provider_name')
    if provider_name is not None and provider_name != '':
        if not isinstance(provider_name, str):
            raise SerializationError("Field 'provider_name' must be a string.")
        kwargs['provider_name'] = provider_name
    return kwargs


def serialize_telemetry(telemetry: AIExecutionTelemetry | None):
    if telemetry is None:
        return None
    return {
        'provider': telemetry.provider,
        'model': telemetry.model,
        'started_at': (
            telemetry.started_at.isoformat() if telemetry.started_at else None
        ),
        'finished_at': (
            telemetry.finished_at.isoformat() if telemetry.finished_at else None
        ),
        'duration_ms': telemetry.duration_ms,
        'success': telemetry.success,
        'error_type': telemetry.error_type,
        'prompt_length': telemetry.prompt_length,
        'response_length': telemetry.response_length,
        'token_usage': telemetry.token_usage,
        'estimated_cost': telemetry.estimated_cost,
        'metadata': dict(telemetry.metadata),
    }


def serialize_editorial_draft(draft):
    """Serialize an ``EditorialDraft`` to a plain JSON-safe dict."""
    return {
        'title': draft.title,
        'body': draft.body,
        'summary': draft.summary,
        'language': draft.language,
        'metadata': dict(draft.metadata),
        'telemetry': serialize_telemetry(draft.telemetry),
    }


def serialize_error(code, message, details=None):
    payload = {
        'error': {
            'code': code,
            'message': message,
        }
    }
    if details is not None:
        payload['error']['details'] = details
    return payload
