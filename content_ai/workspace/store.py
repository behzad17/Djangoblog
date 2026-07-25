"""Django session-backed store for workspace sessions."""

from __future__ import annotations

from content_ai.workspace.session import (
    ArticleSections,
    HistoryEntry,
    WorkspaceSession,
    utc_now,
)
from content_ai.workflow.states import WorkflowState
from datetime import datetime

SESSION_KEY = 'content_ai_editorial_workspace'


def save_session(request, session: WorkspaceSession) -> None:
    request.session[SESSION_KEY] = session.to_dict()
    request.session.modified = True


def load_session(request) -> WorkspaceSession | None:
    raw = request.session.get(SESSION_KEY)
    if not raw:
        return None
    try:
        state = WorkflowState(raw.get('workflow_state') or 'idea')
    except ValueError:
        state = WorkflowState.IDEA
    history: list[HistoryEntry] = []
    for item in raw.get('history') or []:
        created = item.get('created_at')
        try:
            created_at = (
                datetime.fromisoformat(created) if created else utc_now()
            )
        except ValueError:
            created_at = utc_now()
        history.append(
            HistoryEntry(
                entry_id=item.get('entry_id') or '',
                label=item.get('label') or 'Revision',
                sections=ArticleSections.from_dict(item.get('sections')),
                explanation=item.get('explanation') or '',
                created_at=created_at,
            )
        )
    return WorkspaceSession(
        session_id=raw.get('session_id') or '',
        workflow_state=state,
        language=raw.get('language') or 'fa',
        audience=raw.get('audience') or '',
        source_material=raw.get('source_material') or '',
        source_url=raw.get('source_url') or '',
        research_notes=raw.get('research_notes') or '',
        sections=ArticleSections.from_dict(raw.get('sections')),
        history=history,
        last_explanations=list(raw.get('last_explanations') or []),
        metadata=dict(raw.get('metadata') or {}),
    )
