"""Lightweight JSON serializers for the internal Content AI API.

No Django REST Framework — keep the surface minimal and dependency-free.
"""

from __future__ import annotations

from content_ai.telemetry import AIExecutionTelemetry

# Public request fields for the AI Blog Writer editorial draft endpoint.
EDITORIAL_DRAFT_REQUEST_FIELDS = (
    'title',
    'language',
    'category',
    'context',
    'instructions',
)

# Still accepted for PostGenerationRequest mapping / internal testing.
_OPTIONAL_REQUEST_FIELDS = (
    'source',
    'provider_name',
)

_SENSITIVE_METADATA_KEYS = frozenset(
    {
        'prompt',
        'prompt_text',
        'raw_prompt',
    }
)


class SerializationError(ValueError):
    """Raised when request JSON cannot be normalized."""


def parse_editorial_draft_request(data):
    """
    Normalize JSON into kwargs for ``EditorialAIService.generate_draft``.

    Primary fields: title, language, category, context, instructions.
    Optional: source, provider_name.
    """
    if data is None:
        raise SerializationError('Request body is required.')
    if not isinstance(data, dict):
        raise SerializationError('Request body must be a JSON object.')

    allowed = set(EDITORIAL_DRAFT_REQUEST_FIELDS) | set(_OPTIONAL_REQUEST_FIELDS)
    unknown = set(data.keys()) - allowed
    if unknown:
        raise SerializationError(
            f"Unknown fields: {', '.join(sorted(unknown))}."
        )

    kwargs = {}
    for field in EDITORIAL_DRAFT_REQUEST_FIELDS + ('source',):
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


def sanitize_metadata(metadata):
    """Remove prompt strings and other sensitive keys from API metadata."""
    if not metadata:
        return {}
    return {
        key: value
        for key, value in dict(metadata).items()
        if key not in _SENSITIVE_METADATA_KEYS
    }


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
        'metadata': sanitize_metadata(telemetry.metadata),
    }


def serialize_editorial_draft(draft):
    """Serialize an ``EditorialDraft`` to a plain JSON-safe dict."""
    return {
        'title': draft.title,
        'lead': getattr(draft, 'lead', '') or '',
        'body': draft.body,
        'summary': draft.summary,
        'language': draft.language,
        'metadata': sanitize_metadata(draft.metadata),
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
