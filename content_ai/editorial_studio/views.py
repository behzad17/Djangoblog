"""Editorial Studio views — News Import (ES-001)."""

from __future__ import annotations

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from content_ai.config.ai_engine import ENABLE_EDITORIAL_STUDIO
from content_ai.editorial_studio.services import NewsImportService
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
    ProviderNotFound,
)
from content_ai.serializers import serialize_error
from content_ai.source.extract import ArticleExtractionError


def user_can_access_editorial_studio(user) -> bool:
    return bool(user and user.is_authenticated and user.is_staff)


def _json_body(request) -> dict:
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (TypeError, ValueError, UnicodeDecodeError):
        return {}


@staff_member_required
@require_GET
def editorial_studio(request):
    """Render Editorial Studio — News Import page."""
    if not user_can_access_editorial_studio(request.user):
        raise PermissionDenied('Editorial Studio is for staff only.')
    if not ENABLE_EDITORIAL_STUDIO:
        return render(
            request,
            'admin/content_ai/editorial_studio_disabled.html',
            {'title': 'Editorial Studio'},
        )
    return render(
        request,
        'admin/content_ai/editorial_studio.html',
        {
            'title': 'Editorial Studio — News Import',
            'api_url': reverse('content_ai:editorial_studio_import'),
            'workspace_url': reverse('content_ai:editorial_workspace'),
            'studio_url': reverse('content_ai:ai_studio'),
        },
    )


@staff_member_required
@require_POST
def editorial_studio_import(request):
    """JSON API: paste URL → Persian draft via production workflow."""
    if not user_can_access_editorial_studio(request.user):
        return JsonResponse(
            serialize_error(
                'forbidden',
                'Editorial Studio is for staff only.',
            ),
            status=403,
        )
    if not ENABLE_EDITORIAL_STUDIO:
        return JsonResponse(
            serialize_error(
                'editorial_studio_disabled',
                'Editorial Studio is disabled.',
            ),
            status=403,
        )

    payload = _json_body(request)
    url = payload.get('url') or ''
    provider_name = payload.get('provider_name') or None
    if provider_name == '':
        provider_name = None

    try:
        result = NewsImportService().import_news(
            url,
            provider_name=provider_name,
        )
        return JsonResponse({'ok': True, 'result': result})
    except ArticleExtractionError as exc:
        return JsonResponse(
            serialize_error('extraction_failed', str(exc)),
            status=400,
        )
    except (ProviderNotFound, ProviderConfigurationError) as exc:
        return JsonResponse(
            serialize_error('provider_error', str(exc)),
            status=502,
        )
    except GenerationError as exc:
        return JsonResponse(
            serialize_error('generation_failed', str(exc)),
            status=502,
        )
    except Exception as exc:  # noqa: BLE001
        return JsonResponse(
            serialize_error(
                'unexpected_error',
                'News import failed unexpectedly.',
                details=str(exc),
            ),
            status=500,
        )
