"""Django session-backed store for AI Studio sessions."""

from __future__ import annotations

from content_ai.studio.session import GenerationRecord, StudioSession, utc_now
from datetime import datetime

SESSION_KEY = 'content_ai_studio'


def save_session(request, session: StudioSession) -> None:
    request.session[SESSION_KEY] = session.to_dict()
    request.session.modified = True


def load_session(request) -> StudioSession | None:
    raw = request.session.get(SESSION_KEY)
    if not raw:
        return None
    history = [
        GenerationRecord.from_dict(item) for item in (raw.get('history') or [])
    ]
    updated = raw.get('updated_at')
    try:
        updated_at = datetime.fromisoformat(updated) if updated else utc_now()
    except ValueError:
        updated_at = utc_now()
    return StudioSession(
        session_id=raw.get('session_id') or '',
        environment=raw.get('environment') or 'testing',
        active_module=raw.get('active_module') or 'prompt_lab',
        history=history,
        last_comparison=dict(raw.get('last_comparison') or {}),
        last_explanations=list(raw.get('last_explanations') or []),
        metadata=dict(raw.get('metadata') or {}),
        updated_at=updated_at,
    )
