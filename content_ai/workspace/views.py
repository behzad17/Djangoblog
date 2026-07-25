"""AI Editorial Workspace views (APF-001)."""

from __future__ import annotations

import json

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from content_ai.config.ai_engine import ENABLE_AI_EDITORIAL_WORKSPACE
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
    ProviderNotFound,
)
from content_ai.serializers import serialize_error
from content_ai.workflow.states import WorkflowState
from content_ai.workspace.actions import list_actions_for_ui
from content_ai.workspace.services import WorkspaceService
from content_ai.workspace.session import ArticleSections
from content_ai.workspace.store import load_session, save_session


def _json_body(request) -> dict:
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except (TypeError, ValueError, UnicodeDecodeError):
        return {}


def _ensure_session(request):
    service = WorkspaceService()
    session = load_session(request)
    if session is None:
        session = service.new_session()
        save_session(request, session)
    return service, session


def _apply_sections_payload(session, payload: dict) -> None:
    sections = payload.get('sections') or {}
    if sections:
        current = session.sections.to_dict()
        for key, value in sections.items():
            if key in current:
                current[key] = value
        session.sections = ArticleSections.from_dict(current)
    if 'research_notes' in payload and payload.get('research_notes') is not None:
        session.research_notes = str(payload.get('research_notes') or '')
    session.touch()


@staff_member_required
@require_GET
def editorial_workspace(request):
    """Render the AI Editorial Workspace (staff only)."""
    if not ENABLE_AI_EDITORIAL_WORKSPACE:
        return render(
            request,
            'admin/content_ai/editorial_workspace_disabled.html',
            {'title': 'AI Editorial Workspace'},
        )
    service, session = _ensure_session(request)
    return render(
        request,
        'admin/content_ai/editorial_workspace.html',
        {
            'title': 'AI Editorial Workspace',
            'session': session.to_dict(),
            'actions': list_actions_for_ui(),
            'workflow_states': [
                {'id': s.value, 'label': s.value.replace('_', ' ').title()}
                for s in (
                    WorkflowState.RESEARCHING,
                    WorkflowState.DRAFTING,
                    WorkflowState.REVIEWING,
                    WorkflowState.REVISION_REQUIRED,
                    WorkflowState.READY_FOR_APPROVAL,
                    WorkflowState.APPROVED,
                )
            ],
            'api_base': reverse(
                'content_ai:workspace_api', kwargs={'action': 'reset'}
            ).rsplit('reset', 1)[0],
        },
    )


@staff_member_required
@require_POST
def workspace_api(request, action: str):
    """JSON API for workspace panel actions."""
    if not ENABLE_AI_EDITORIAL_WORKSPACE:
        return JsonResponse(
            serialize_error(
                'workspace_disabled',
                'AI Editorial Workspace is disabled.',
            ),
            status=403,
        )
    service, session = _ensure_session(request)
    payload = _json_body(request)

    try:
        if action == 'ingest_source':
            source = service.ingest_source(
                session,
                url=payload.get('source_url') or payload.get('url') or '',
                text=payload.get('source_text') or payload.get('text') or '',
                title=payload.get('title') or '',
                publisher=payload.get('publisher') or '',
            )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'source': source, 'session': session.to_dict()}
            )

        if action in ('generate_draft', 'generate'):
            _apply_sections_payload(session, payload)
            if payload.get('source_text') or payload.get('source_url'):
                service.ingest_source(
                    session,
                    url=payload.get('source_url') or '',
                    text=payload.get('source_text') or session.source_material,
                    title=payload.get('title') or '',
                    publisher=payload.get('publisher') or '',
                )
            service.generate_draft(
                session,
                title=payload.get('title') or session.sections.headline,
                category=payload.get('category') or '',
                instructions=payload.get('instructions') or '',
                provider_name=payload.get('provider') or None,
            )
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': session.to_dict()})

        if action == 'regenerate_section':
            _apply_sections_payload(session, payload)
            service.regenerate_section(
                session,
                payload.get('section') or 'body',
                instructions=payload.get('instructions') or '',
                provider_name=payload.get('provider') or None,
            )
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': session.to_dict()})

        if action in ('run_action', 'assistant_action'):
            _apply_sections_payload(session, payload)
            service.run_assistant_action(
                session,
                payload.get('action_id') or '',
                provider_name=payload.get('provider') or None,
            )
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': session.to_dict()})

        if action == 'fact_check':
            _apply_sections_payload(session, payload)
            report = service.fact_check(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'fact_check': report, 'session': session.to_dict()}
            )

        if action == 'evaluate':
            _apply_sections_payload(session, payload)
            report = service.evaluate(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'evaluation': report, 'session': session.to_dict()}
            )

        if action in ('prepare_seo', 'seo'):
            _apply_sections_payload(session, payload)
            report = service.seo_placeholders(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'seo': report, 'session': session.to_dict()}
            )

        if action in ('set_workflow', 'workflow'):
            target = WorkflowState(payload.get('state') or 'reviewing')
            service.advance_workflow(session, target)
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': session.to_dict()})

        if action == 'update_sections':
            _apply_sections_payload(session, payload)
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': session.to_dict()})

        if action == 'import_article':
            service.import_existing_article(
                session,
                post_id=payload.get('post_id'),
            )
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': session.to_dict()})

        if action == 'restore_history':
            ok = session.restore_history(payload.get('entry_id') or '')
            save_session(request, session)
            return JsonResponse({'ok': ok, 'session': session.to_dict()})

        if action == 'reset':
            session = service.new_session(
                language=payload.get('language') or 'fa',
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
