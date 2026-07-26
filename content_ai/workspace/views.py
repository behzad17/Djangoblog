"""AI Editorial Workspace views (APF-001)."""

from __future__ import annotations

import json
import logging
import traceback

from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

logger = logging.getLogger(__name__)

from content_ai.config.ai_engine import ENABLE_AI_EDITORIAL_WORKSPACE
from content_ai.editorial.article_length import list_article_lengths_for_ui
from content_ai.editorial.category_recommender import list_blog_categories_for_ui
from content_ai.editorial.content_types import (
    list_content_types_for_ui,
    list_goals_for_ui,
    list_styles_for_ui,
)
from content_ai.providers.exceptions import (
    GenerationError,
    ProviderConfigurationError,
    ProviderNotFound,
)
from content_ai.serializers import serialize_error
from content_ai.workflow.states import WorkflowState
from content_ai.source.extract import ArticleExtractionError
from content_ai.workspace.actions import list_actions_for_ui
from content_ai.workspace.integrity import SourceIntegrityError
from content_ai.workspace.services import WorkspaceService
from content_ai.workspace.session import ArticleSections
from content_ai.workspace.store import load_session, save_session


def _session_payload(service: WorkspaceService, session) -> dict:
    payload = session.to_dict()
    payload['actions'] = service.assistant_actions(session)
    return payload


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
    response = render(
        request,
        'admin/content_ai/editorial_workspace.html',
        {
            'title': 'AI Editorial Workspace',
            'session': _session_payload(service, session),
            'actions': list_actions_for_ui(session.resolved_content_type()),
            'content_types': list_content_types_for_ui(),
            'editorial_goals': list_goals_for_ui(),
            'writing_styles': list_styles_for_ui(),
            'article_lengths': list_article_lengths_for_ui(),
            'blog_categories': list_blog_categories_for_ui(),
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
    # Prevent BFCache from resurrecting a stale pre-reset workspace DOM.
    response['Cache-Control'] = 'no-store'
    return response


@staff_member_required
@require_POST
def workspace_api(request, action: str):
    """JSON API for workspace panel actions."""
    logger.info(
        'workspace_api ENTER method=%s action=%r path=%s user=%s',
        request.method,
        action,
        request.path,
        getattr(request.user, 'username', None),
    )
    if not ENABLE_AI_EDITORIAL_WORKSPACE:
        logger.warning('workspace_api blocked: workspace disabled')
        return JsonResponse(
            serialize_error(
                'workspace_disabled',
                'AI Editorial Workspace is disabled.',
            ),
            status=403,
        )
    service, session = _ensure_session(request)
    payload = _json_body(request)
    logger.info(
        'workspace_api session=%s payload_keys=%s',
        getattr(session, 'session_id', None),
        sorted(payload.keys()) if isinstance(payload, dict) else type(payload),
    )

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
                {
                    'ok': True,
                    'source': source,
                    'session': _session_payload(service, session),
                }
            )

        if action in ('set_classification', 'classification'):
            service.set_classification(
                session,
                content_type=payload.get('content_type'),
                goal=payload.get('goal'),
                writing_style=payload.get('writing_style')
                or payload.get('style'),
                article_length=payload.get('article_length'),
            )
            if payload.get('regenerate'):
                service.generate_draft(
                    session,
                    title=payload.get('title') or session.sections.headline,
                    category=payload.get('category') or '',
                    instructions=payload.get('instructions') or '',
                    provider_name=payload.get('provider') or None,
                    article_length=payload.get('article_length'),
                )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'session': _session_payload(service, session)}
            )

        if action in ('generate_draft', 'generate'):
            _apply_sections_payload(session, payload)
            if payload.get('content_type') or payload.get('goal') or payload.get(
                'writing_style'
            ) or payload.get('style') or payload.get('article_length'):
                service.set_classification(
                    session,
                    content_type=payload.get('content_type'),
                    goal=payload.get('goal'),
                    writing_style=payload.get('writing_style')
                    or payload.get('style'),
                    article_length=payload.get('article_length'),
                )
            # Never silently reuse previous session text for a new URL.
            # Use exactly what the client sent for URL/text; empty stays empty.
            if 'source_text' in payload or 'source_url' in payload:
                incoming_url = (
                    payload['source_url']
                    if 'source_url' in payload
                    else (session.source_url or '')
                )
                if 'source_text' in payload:
                    incoming_text = payload.get('source_text') or ''
                elif (incoming_url or '').strip() != (session.source_url or '').strip():
                    # URL changed without a text field — do not keep old article body.
                    incoming_text = ''
                else:
                    incoming_text = session.source_material or ''
                service.ingest_source(
                    session,
                    url=incoming_url or '',
                    text=incoming_text,
                    title=payload.get('title') or '',
                    publisher=payload.get('publisher') or '',
                )
            service.generate_draft(
                session,
                title=payload.get('title') or '',
                category=payload.get('category') or '',
                instructions=payload.get('instructions') or '',
                provider_name=payload.get('provider') or None,
                article_length=payload.get('article_length'),
            )
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'session': _session_payload(service, session)}
            )

        if action == 'regenerate_section':
            _apply_sections_payload(session, payload)
            service.regenerate_section(
                session,
                payload.get('section') or 'body',
                instructions=payload.get('instructions') or '',
                provider_name=payload.get('provider') or None,
            )
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': _session_payload(service, session)})

        if action in ('run_action', 'assistant_action'):
            _apply_sections_payload(session, payload)
            service.run_assistant_action(
                session,
                payload.get('action_id') or '',
                provider_name=payload.get('provider') or None,
            )
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': _session_payload(service, session)})

        if action == 'fact_check':
            _apply_sections_payload(session, payload)
            report = service.fact_check(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'fact_check': report, 'session': _session_payload(service, session)}
            )

        if action == 'evaluate':
            _apply_sections_payload(session, payload)
            report = service.evaluate(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'evaluation': report, 'session': _session_payload(service, session)}
            )

        if action in ('prepare_seo', 'seo'):
            _apply_sections_payload(session, payload)
            report = service.seo_placeholders(session)
            save_session(request, session)
            return JsonResponse(
                {'ok': True, 'seo': report, 'session': _session_payload(service, session)}
            )

        if action in ('set_workflow', 'workflow'):
            target = WorkflowState(payload.get('state') or 'reviewing')
            service.advance_workflow(session, target)
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': _session_payload(service, session)})

        if action == 'update_sections':
            _apply_sections_payload(session, payload)
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': _session_payload(service, session)})

        if action in ('save_draft', 'save_blog_draft', 'save'):
            logger.info('workspace_api SAVE_DRAFT step=apply_sections')
            _apply_sections_payload(session, payload)
            logger.info(
                'workspace_api SAVE_DRAFT step=call_save_blog_draft '
                'headline=%r lead_len=%s body_len=%s',
                (session.sections.headline or '')[:80],
                len(session.sections.lead or ''),
                len(session.sections.body or ''),
            )
            blog_draft = service.save_blog_draft(session, user=request.user)
            logger.info(
                'workspace_api SAVE_DRAFT step=save_ok blog_draft=%s',
                blog_draft,
            )
            save_session(request, session)
            return JsonResponse(
                {
                    'ok': True,
                    'blog_draft': blog_draft,
                    'session': _session_payload(service, session),
                }
            )

        if action in ('publish_draft', 'publish_blog_draft', 'publish'):
            _apply_sections_payload(session, payload)
            published = service.publish_blog_draft(session, user=request.user)
            save_session(request, session)
            return JsonResponse(
                {
                    'ok': True,
                    'published': published,
                    'session': _session_payload(service, session),
                }
            )

        if action == 'import_article':
            service.import_existing_article(
                session,
                post_id=payload.get('post_id'),
            )
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': _session_payload(service, session)})

        if action == 'restore_history':
            ok = session.restore_history(payload.get('entry_id') or '')
            save_session(request, session)
            return JsonResponse({'ok': ok, 'session': _session_payload(service, session)})

        if action == 'reset':
            session = service.new_session(
                language=payload.get('language') or 'fa',
            )
            save_session(request, session)
            return JsonResponse({'ok': True, 'session': _session_payload(service, session)})

        return JsonResponse(
            serialize_error('unknown_action', f'Unknown action: {action}'),
            status=400,
        )

    except SourceIntegrityError as exc:
        logger.warning(
            'workspace_api source_integrity action=%r session=%s: %s',
            action,
            getattr(session, 'session_id', None),
            exc,
        )
        return JsonResponse(
            serialize_error('source_not_ready', str(exc)),
            status=400,
        )
    except ArticleExtractionError as exc:
        logger.warning(
            'workspace_api extraction_failed action=%r session=%s: %s',
            action,
            getattr(session, 'session_id', None),
            exc,
        )
        return JsonResponse(
            serialize_error('extraction_failed', str(exc)),
            status=400,
        )
    except (ProviderNotFound, ProviderConfigurationError, GenerationError) as exc:
        logger.exception('workspace_api generation_failed action=%r', action)
        return JsonResponse(
            serialize_error('generation_failed', str(exc)),
            status=502,
        )
    except ValueError as exc:
        logger.warning('workspace_api validation_error action=%r: %s', action, exc)
        return JsonResponse(
            serialize_error('validation_error', str(exc)),
            status=400,
        )
    except Exception as exc:
        logger.error(
            'workspace_api internal_error action=%r: %s\n%s',
            action,
            exc,
            traceback.format_exc(),
        )
        return JsonResponse(
            serialize_error('internal_error', str(exc)),
            status=500,
        )
