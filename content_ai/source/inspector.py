"""Source inspector stub — no external retrieval (RFC-006 / APF-001)."""

from __future__ import annotations

from content_ai.source.models import SourceRecord, create_source_record


class SourceInspector:
    """
    Inspect manually supplied source material.

    Does not fetch URLs. Classifies pasted text / URL strings lightly.
    """

    def inspect(
        self,
        *,
        url: str = '',
        text: str = '',
        title: str = '',
        publisher: str = '',
        language: str = '',
    ) -> SourceRecord:
        warnings = ['Trust score is a placeholder.', 'No external retrieval.']
        source_type = 'url' if (url or '').strip() else 'text'
        if (url or '').strip() and not (text or '').strip():
            warnings.append(
                'URL recorded only — content was not fetched automatically.'
            )
        detected_language = language or ''
        # Very light heuristic for Persian script presence.
        sample = text or title or ''
        if any('\u0600' <= c <= '\u06FF' for c in sample):
            detected_language = detected_language or 'fa'
        return create_source_record(
            title=title or (url[:80] if url else 'Untitled source'),
            publisher=publisher,
            url=url,
            detected_language=detected_language,
            source_type=source_type,
            trust_score=None,
            raw_text=text,
            warnings=warnings,
            metadata={'inspector': 'stub'},
        )
