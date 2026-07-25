"""AI Studio views (APF-002) — administrators / staff only."""

from __future__ import annotations

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from content_ai.config.ai_engine import ENABLE_AI_STUDIO
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
    ProviderNotFound,
)
from content_ai.serializers import serialize_error
from content_ai.studio.modules import list_modules_for_ui
from content_ai.studio.services import StudioService
from content_ai.studio.store import load_session, save_session


def user_can_access_studio(user) -> bool:
    """Studio is for Admin editors/administrators — never public."""
    return bool(
        user
        and user.is_authenticated
        and user.is_staff
    )


def _json_body(request) -> dict:
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (TypeError, ValueError, UnicodeDecodeError):
        return {}


def _ensure_session(request):
    service = StudioService()
    session = load_session(request)
    if session is None:
        session = service.new_session()
        save_session(request, session)
    return service, session


@staff_member_required
@require_GET
def ai_studio(request):
    """Render the AI Studio control centre."""
    if not user_can_access_studio(request.user):
        raise PermissionDenied('AI Studio is for administrators only.')
    if not ENABLE_AI_STUDIO:
        return render(
            request,
            'admin/content_ai/ai_studio_disabled.html',
            {'title': 'AI Studio'},
        )
    service, session = _ensure_session(request)
    return render(
        request,
        'admin/content_ai/ai_studio.html',
        {
            'title': 'AI Studio',
            'session': session.to_dict(),
            'modules': list_modules_for_ui(),
            'prompt_options': service.list_prompt_options(),
            'api_base': reverse(
                'content_ai:studio_api', kwargs={'action': 'reset'}
            ).rsplit('reset', 1)[0],
            'workspace_url': reverse('content_ai:editorial_workspace'),
        },
    )


@staff_member_required
@require_POST
def studio_api(request, action: str):
    """JSON API for Studio lab actions."""
    if not user_can_access_studio(request.user):
        return JsonResponse(
            serialize_error('forbidden', 'AI Studio is for administrators only.'),
            status=403,
        )
    if not ENABLE_AI_STUDIO:
        return JsonResponse(
            serialize_error('studio_disabled', 'AI Studio is disabled.'),
            status=403,
        )
    service, session = _ensure_session(request)
    payload = _json_body(request)

    try:
        if action == 'set_environment':
            session.set_environment(payload.get('environment') or 'testing')
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': session.to_dict()})

        if action == 'set_module':
            session.active_module = payload.get('module') or 'prompt_lab'
            session.touch()
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': session.to_dict()})

        if action == 'prompt_preview':
            result = service.preview_prompt(
                session,
                version=payload.get('version') or 'v1',
                style=payload.get('style') or 'news',
                user_prompt=payload.get('user_prompt') or '',
            )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'prompt_compare':
            result = service.compare_prompts(
                session,
                version_a=payload.get('version_a') or 'v1',
                style_a=payload.get('style_a') or 'news',
                version_b=payload.get('version_b') or 'v1',
                style_b=payload.get('style_b') or 'analysis',
                user_prompt=payload.get('user_prompt') or '',
            )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'knowledge_browse':
            result = service.browse_knowledge(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'knowledge_compare':
            result = service.compare_knowledge(
                session,
                pack_a=payload.get('pack_a') or '',
                pack_b=payload.get('pack_b') or '',
            )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'provider_inspect':
            result = service.inspect_providers(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'evaluate':
            result = service.evaluate_text(
                session,
                output_text=payload.get('output_text') or '',
                input_text=payload.get('input_text') or '',
                prompt_version=payload.get('prompt_version') or '',
                knowledge_version=payload.get('knowledge_version') or '',
                provider=payload.get('provider') or 'studio',
            )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'workflow_inspect':
            result = service.inspect_workflow(
                session,
                state=payload.get('state') or 'idea',
                title=payload.get('title') or 'Studio inspection',
            )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'run_test':
            result = service.run_test_generation(
                session,
                user_prompt=payload.get('user_prompt') or '',
                version=payload.get('version') or 'v1',
                style=payload.get('style') or 'news',
                provider_name=payload.get('provider') or 'mock',
                knowledge_version=payload.get('knowledge_version') or '',
            )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'history':
            result = service.generation_history(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'compare_generations':
            result = service.compare_generations(
                session,
                generation_id_a=payload.get('generation_id_a') or '',
                generation_id_b=payload.get('generation_id_b') or '',
            )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'system_health':
            result = service.system_health(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'result': result, 'session': session.to_dict()}
            )

        if action == 'reset':
            session = service.new_session(
                environment=payload.get('environment') or 'testing',
            )
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': session.to_dict()})

        return JsonResponse(
            serialize_error('unknown_action', f'Unknown action: {action}'),
            status=400,
        )

    except (ProviderNotFound, ProviderConfigurationError, GenerationError) as exc:
        return JsonResponse(
            serialize_error('generation_failed', str(exc)),
            status=502,
        )
    except ValueError as exc:
        return JsonResponse(
            serialize_error('validation_error', str(exc)),
            status=400,
        )
    except Exception as exc:
        return JsonResponse(
            serialize_error('internal_error', str(exc)),
            status=500,
        )
