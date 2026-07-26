"""Parse labelled TITLE/LEAD/BODY AI output into draft sections."""

from __future__ import annotations

import re

_SECTION_PATTERN = re.compile(
    r'^(TITLE|LEAD|BODY|SUMMARY|CATEGORY|TAGS)\s*:\s*',
    re.IGNORECASE | re.MULTILINE,
)


def parse_structured_draft(raw: str, *, fallback_title: str = '') -> dict:
    """Parse labelled AI output into title/lead/body/summary/category/tags.

    When labelled sections are present, missing BODY is left empty rather than
    dumping the whole raw string (which would leak TITLE/LEAD labels into body).
    """
    text = (raw or '').strip()
    if not text:
        return {
            'title': fallback_title or '',
            'lead': '',
            'body': '',
            'summary': '',
            'suggested_category': 'news',
            'suggested_tags': [],
        }

    matches = list(_SECTION_PATTERN.finditer(text))
    sections: dict[str, str] = {}
    if matches:
        for index, match in enumerate(matches):
            key = match.group(1).upper()
            start = match.end()
            end = (
                matches[index + 1].start()
                if index + 1 < len(matches)
                else len(text)
            )
            sections[key] = text[start:end].strip()
    else:
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', text) if p.strip()]
        lead = paragraphs[0] if paragraphs else text
        body = '\n\n'.join(paragraphs[1:]) if len(paragraphs) > 1 else ''
        sections = {
            'TITLE': '',
            'LEAD': lead,
            'BODY': body,
            'SUMMARY': lead,
            'CATEGORY': 'news',
            'TAGS': '',
        }

    tags_raw = sections.get('TAGS', '')
    tags = [
        part.strip()
        for part in re.split(r'[,،\n]+', tags_raw)
        if part.strip()
    ]
    title = (sections.get('TITLE') or '').strip()
    lead = (sections.get('LEAD') or '').strip()
    body = (sections.get('BODY') or '').strip()
    if not title and not matches:
        # Unlabelled single-block output: keep as lead; do not invent a title
        # from the source language fallback until the caller decides.
        title = ''
    return {
        'title': title or (fallback_title or ''),
        'lead': lead,
        'body': body,
        'summary': (
            (sections.get('SUMMARY') or '').strip() or lead
        ),
        'suggested_category': (
            sections.get('CATEGORY') or 'news'
        ).strip().lower() or 'news',
        'suggested_tags': tags,
    }


__all__ = ['parse_structured_draft']
