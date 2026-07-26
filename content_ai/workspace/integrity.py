"""Source / session integrity guards for Editorial Workspace generation."""

from __future__ import annotations

import hashlib
import logging
from typing import Any

logger = logging.getLogger(__name__)

SOURCE_NOT_READY_MESSAGE = (
    'Source content has not been imported yet. '
    'Please ingest the source or paste the article text.'
)

SOURCE_MISMATCH_MESSAGE = (
    'Source URL or text does not match this workspace session. '
    'Re-ingest the source or start a new session before generating.'
)


class SourceIntegrityError(ValueError):
    """Raised when generation would use empty or mismatched source material."""


def fingerprint_text(text: str) -> str:
    return hashlib.sha256((text or '').encode('utf-8')).hexdigest()


def build_source_binding(
    *,
    session_id: str,
    source_url: str = '',
    source_text: str = '',
    retrieval: str = 'manual_paste',
) -> dict[str, Any]:
    material = (source_text or '').strip()
    return {
        'session_id': session_id,
        'source_url': (source_url or '').strip(),
        'source_text_sha256': fingerprint_text(material) if material else '',
        'source_text_chars': len(material),
        'retrieval': retrieval,
    }


def log_generation_source(
    *,
    session_id: str,
    source_url: str,
    source_text: str,
    binding: dict | None = None,
) -> None:
    material = source_text or ''
    logger.info(
        'workspace_generate_source session_id=%s source_url=%r '
        'source_chars=%s source_sha256=%s binding_session=%s binding_url=%r '
        'source_text=%r',
        session_id,
        source_url or '',
        len(material),
        fingerprint_text(material.strip()) if material.strip() else '',
        (binding or {}).get('session_id'),
        (binding or {}).get('source_url'),
        material[:8000],
    )


def assert_generation_integrity(session) -> None:
    """Abort generation unless current URL, source text, and session align."""
    material = (getattr(session, 'source_material', None) or '').strip()
    url = (getattr(session, 'source_url', None) or '').strip()
    metadata = getattr(session, 'metadata', None) or {}
    binding = dict(metadata.get('source_binding') or {})
    source_meta = dict(metadata.get('source') or {})
    warnings = list(source_meta.get('warnings') or [])

    log_generation_source(
        session_id=getattr(session, 'session_id', ''),
        source_url=url,
        source_text=material,
        binding=binding,
    )

    if not material:
        raise SourceIntegrityError(SOURCE_NOT_READY_MESSAGE)

    if any('URL recorded only' in str(item) for item in warnings) and not material:
        raise SourceIntegrityError(SOURCE_NOT_READY_MESSAGE)

    retrieval = binding.get('retrieval') or ''
    if retrieval == 'url_only_no_fetch':
        raise SourceIntegrityError(SOURCE_NOT_READY_MESSAGE)

    bound_session = (binding.get('session_id') or '').strip()
    if bound_session and bound_session != getattr(session, 'session_id', ''):
        raise SourceIntegrityError(SOURCE_MISMATCH_MESSAGE)

    bound_url = (binding.get('source_url') or '').strip()
    if url and bound_url and url != bound_url:
        raise SourceIntegrityError(SOURCE_MISMATCH_MESSAGE)

    meta_url = (source_meta.get('url') or '').strip()
    if url and meta_url and url != meta_url:
        raise SourceIntegrityError(SOURCE_MISMATCH_MESSAGE)

    expected_fp = (binding.get('source_text_sha256') or '').strip()
    if expected_fp:
        actual_fp = fingerprint_text(material)
        if actual_fp != expected_fp:
            raise SourceIntegrityError(SOURCE_MISMATCH_MESSAGE)

    logger.info(
        'workspace_generate_integrity_ok session_id=%s source_url=%r chars=%s',
        getattr(session, 'session_id', ''),
        url,
        len(material),
    )
