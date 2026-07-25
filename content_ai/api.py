"""Internal AI Integration API (staff/superuser only, no persistence)."""

from __future__ import annotations

import json
import logging

from django.http import JsonResponse
from django.views.decorators.http import require_POST

from content_ai.editorial.service import EditorialAIService
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
    ProviderNotFound,
)
from content_ai.serializers import (
    SerializationError,
    parse_editorial_draft_request,
    serialize_editorial_draft,
    serialize_error,
    serialize_telemetry,
)

logger = logging.getLogger(__name__)


def _user_can_access_internal_api(user):
    """Authenticated staff or superuser only."""
    return bool(
        getattr(user, 'is_authenticated', False)
        and (user.is_staff or user.is_superuser)
    )


@require_POST
def create_editorial_draft(request):
    """
    POST /api/internal/ai/editorial/draft/

    Internal AI Integration API: invokes ``EditorialAIService.generate_draft``
    and returns an in-memory ``EditorialDraft`` JSON payload. Nothing is saved.
    Not a public endpoint.
    """
    if not request.user.is_authenticated:
        return JsonResponse(
            serialize_error('unauthorized', 'Authentication required.'),
            status=401,
        )
    if not _user_can_access_internal_api(request.user):
        return JsonResponse(
            serialize_error('forbidden', 'Staff access required.'),
            status=403,
        )

    try:
        payload = json.loads(request.body.decode('utf-8') or '{}')
    except (UnicodeDecodeError, json.JSONDecodeError):
        return JsonResponse(
            serialize_error('invalid_json', 'Request body must be valid JSON.'),
            status=400,
        )

    try:
        kwargs = parse_editorial_draft_request(payload)
    except SerializationError as exc:
        return JsonResponse(
            serialize_error('validation_error', str(exc)),
            status=400,
        )

    try:
        draft = EditorialAIService().generate_draft(**kwargs)
    except ProviderNotFound as exc:
        return JsonResponse(
            serialize_error('provider_not_found', str(exc)),
            status=400,
        )
    except ProviderConfigurationError as exc:
        return JsonResponse(
            serialize_error('provider_configuration_error', str(exc)),
            status=503,
        )
    except GenerationError as exc:
        body = serialize_error('generation_failed', str(exc))
        if getattr(exc, 'telemetry', None) is not None:
            body['telemetry'] = serialize_telemetry(exc.telemetry)
        return JsonResponse(body, status=502)
    except Exception:
        logger.exception('Unexpected failure in internal editorial draft API')
        return JsonResponse(
            serialize_error('internal_error', 'Unexpected server error.'),
            status=500,
        )

    return JsonResponse(serialize_editorial_draft(draft), status=200)
