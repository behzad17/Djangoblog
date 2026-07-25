"""Editorial Studio views — Smart News Import (ES-001A)."""

from __future__ import annotations

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from content_ai.config.ai_engine import ENABLE_EDITORIAL_STUDIO
from content_ai.editorial_studio.services import (
    CONTENT_TYPES,
    OUTPUT_MODES,
    NewsImportService,
)
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


def _editor_message(code: str, fallback: str) -> str:
    messages = {
        'invalid_url': 'Please paste a valid article URL starting with https://.',
        'extraction_failed': (
            'We could not read this article. Try another link or paste a '
            'full article URL.'
        ),
        'generation_failed': (
            'Draft generation failed. Please try again in a moment.'
        ),
        'provider_error': (
            'The AI provider is unavailable right now. Please try again later.'
        ),
    }
    return messages.get(code, fallback)


@staff_member_required
@require_GET
def editorial_studio(request):
    """Render Editorial Studio — Smart News Import page."""
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
    """JSON API: paste URL → structured Persian draft via production workflow."""
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
    content_type = payload.get('content_type') or 'auto'
    output_mode = payload.get('output_mode') or 'publish_ready'
    provider_name = payload.get('provider_name') or None
    if provider_name == '':
        provider_name = None

    if content_type not in CONTENT_TYPES:
        return JsonResponse(
            serialize_error(
                'invalid_content_type',
                'Please choose a valid content type.',
            ),
            status=400,
        )
    if output_mode not in OUTPUT_MODES:
        return JsonResponse(
            serialize_error(
                'invalid_output_mode',
                'Please choose a valid output mode.',
            ),
            status=400,
        )

    try:
        result = NewsImportService().import_news(
            url,
            content_type=content_type,
            output_mode=output_mode,
            provider_name=provider_name,
        )
        return JsonResponse({'ok': True, 'result': result})
    except ArticleExtractionError as exc:
        code = 'invalid_url' if 'http' in str(exc).lower() or 'url' in str(exc).lower() else 'extraction_failed'
        if 'paste' in str(exc).lower() or 'valid' in str(exc).lower():
            code = 'invalid_url'
        return JsonResponse(
            serialize_error(
                code,
                _editor_message(code, str(exc)),
            ),
            status=400,
        )
    except (ProviderNotFound, ProviderConfigurationError) as exc:
        return JsonResponse(
            serialize_error(
                'provider_error',
                _editor_message('provider_error', str(exc)),
            ),
            status=502,
        )
    except GenerationError as exc:
        return JsonResponse(
            serialize_error(
                'generation_failed',
                _editor_message('generation_failed', str(exc)),
            ),
            status=502,
        )
    except Exception:  # noqa: BLE001
        return JsonResponse(
            serialize_error(
                'unexpected_error',
                'News import failed unexpectedly. Please try again.',
            ),
            status=500,
        )
