"""Source Intelligence models (RFC-006 / APF-001)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any
from uuid import uuid4


@dataclass(frozen=True, slots=True)
class SourceRecord:
    """
    Provider-independent source descriptor.

    May contain fetched article text (URL ingest) or manually pasted material.
    """

    source_id: str
    title: str = ''
    publisher: str = ''
    url: str = ''
    publication_date: date | None = None
    detected_language: str = ''
    detected_country: str = ''
    source_type: str = 'unknown'
    trust_score: float | None = None
    freshness: str = 'unknown'
    classification: str = ''
    warnings: tuple[str, ...] = ()
    raw_text: str = ''
    metadata: dict[str, Any] = field(default_factory=dict)


def create_source_record(
    *,
    title: str = '',
    publisher: str = '',
    url: str = '',
    publication_date: date | None = None,
    detected_language: str = '',
    detected_country: str = '',
    source_type: str = 'manual',
    trust_score: float | None = None,
    raw_text: str = '',
    warnings: list[str] | None = None,
    source_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> SourceRecord:
    return SourceRecord(
        source_id=(source_id or str(uuid4())).strip(),
        title=title or '',
        publisher=publisher or '',
        url=url or '',
        publication_date=publication_date,
        detected_language=detected_language or '',
        detected_country=detected_country or '',
        source_type=source_type or 'manual',
        trust_score=trust_score,
        freshness='unknown',
        classification='',
        warnings=tuple(warnings or ('Trust score is a placeholder.',)),
        raw_text=raw_text or '',
        metadata=dict(metadata or {}),
    )
