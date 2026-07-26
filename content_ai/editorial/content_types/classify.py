"""Heuristic content-type classifier (no LLM required)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from content_ai.editorial.content_types.constants import ContentType
from content_ai.editorial.content_types.registry import resolve_content_type


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    content_type: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            'content_type': self.content_type,
            'confidence': round(float(self.confidence), 3),
            'reasons': list(self.reasons),
            'scores': {
                key: round(float(value), 3)
                for key, value in self.scores.items()
            },
        }


_TYPE_SIGNALS: dict[str, tuple[str, ...]] = {
    ContentType.GUIDE: (
        'guide',
        'vägledning',
        'راهنما',
        'how to live',
        'checklist',
        'step by step',
        'steg för steg',
    ),
    ContentType.HOW_TO: (
        'how to',
        'hur man',
        'så gör du',
        'instructions',
        'tutorial',
        'آموزش',
        'چگونه',
    ),
    ContentType.PRESS_RELEASE: (
        'pressmeddelande',
        'press release',
        'press-release',
        'kommuniqué',
        'بیانیه مطبوعاتی',
    ),
    ContentType.ANNOUNCEMENT: (
        'announcement',
        'meddelande',
        'kungörelse',
        'regeringen',
        'myndigheten',
        'förordning',
        'skatteverket',
        'migrationsverket',
        'اطلاعیه',
    ),
    ContentType.INTERVIEW: (
        'intervju',
        'interview',
        'frågor och svar',
        'q&a',
        'مصاحبه',
        'says:',
        'säger:',
    ),
    ContentType.ANALYSIS: (
        'analys',
        'analysis',
        'utredning',
        'implication',
        'تحلیل',
        'research report',
        'studie',
        'forskning',
    ),
    ContentType.REPORT: (
        'rapport',
        'report',
        'key findings',
        'slutsatser',
        'گزارش',
    ),
    ContentType.REPORTAGE: (
        'reportage',
        'feature story',
        'på plats',
        'گزارش میدانی',
    ),
    ContentType.OPINION: (
        'opinion',
        'debatt',
        'ledare',
        'kommentar',
        'viewpoint',
        'نظر',
        'یادداشت',
    ),
    ContentType.EDITORIAL: (
        'editorial',
        'ledare',
        'vår ståndpunkt',
        'سردبیری',
    ),
    ContentType.FAQ: (
        'faq',
        'vanliga frågor',
        'frågor och svar',
        'سوالات متداول',
    ),
    ContentType.EXPLAINER: (
        'explainer',
        'förklarar',
        'what is',
        'vad är',
        'why it matters',
        'توضیح',
        'چرا مهم',
    ),
    ContentType.FEATURE: (
        'feature',
        'långläsning',
        'portrait',
        'پرونده',
    ),
    ContentType.EVENT: (
        'event',
        'evenemang',
        'seminar',
        'workshop',
        'festival',
        'registration open',
        'ثبت‌نام',
        'رویداد',
        'همایش',
    ),
    ContentType.REVIEW: (
        'review',
        'recension',
        'betyg',
        'نقد',
        'بازبینی',
        'stars out of',
    ),
    ContentType.COMMUNITY_STORY: (
        'community story',
        'community',
        'diaspora',
        'local voice',
        'داستان جامعه',
        'جامعه ایرانی',
    ),
    ContentType.NEWS: (
        'nyheter',
        'news',
        'breaking',
        'just nu',
        'خبر',
    ),
}

_URL_HINTS: dict[str, tuple[str, ...]] = {
    ContentType.PRESS_RELEASE: ('/press', '/pressmeddelande', '/press-release'),
    ContentType.ANNOUNCEMENT: (
        'skatteverket.se',
        'migrationsverket.se',
        'regeringen.se',
        '/kungorelse',
    ),
    ContentType.GUIDE: ('/guide', '/vagledning', '/checklist'),
    ContentType.HOW_TO: ('/how-to', '/howto', '/sa-gor-du'),
    ContentType.FAQ: ('/faq', '/vanliga-fragor'),
    ContentType.ANALYSIS: ('/analys', '/analysis', '/rapport'),
    ContentType.INTERVIEW: ('/intervju', '/interview'),
    ContentType.EVENT: ('/event', '/evenemang', '/kalender'),
    ContentType.REVIEW: ('/review', '/recension'),
    ContentType.COMMUNITY_STORY: ('/community', '/diaspora'),
    ContentType.NEWS: ('/nyheter', '/news', '/article'),
}


def _blob(*, title='', text='', url='', publisher='', metadata=None) -> str:
    meta = metadata or {}
    parts = [
        title or '',
        url or '',
        publisher or '',
        str(meta.get('source_type') or ''),
        str(meta.get('og_type') or ''),
        (text or '')[:2500],
    ]
    return ' '.join(parts).lower()


def _score_type(content_type: str, blob: str, url: str) -> tuple[float, list[str]]:
    score = 0.0
    reasons: list[str] = []
    for token in _TYPE_SIGNALS.get(content_type, ()):
        if token in blob:
            score += 1.0
            reasons.append(f'Matched signal “{token}” for {content_type}.')
    for hint in _URL_HINTS.get(content_type, ()):
        if hint in (url or '').lower():
            score += 1.5
            reasons.append(f'URL hint “{hint}” suggests {content_type}.')
    return score, reasons


def classify_content(
    *,
    title: str = '',
    text: str = '',
    url: str = '',
    publisher: str = '',
    metadata: dict | None = None,
    override: str | None = None,
) -> ClassificationResult:
    """Classify editorial content type from source signals.

    If ``override`` is provided, return that type with confidence 1.0.
    """
    if override:
        resolved = resolve_content_type(override)
        return ClassificationResult(
            content_type=resolved,
            confidence=1.0,
            reasons=['Editor override selected this content type.'],
            scores={resolved: 1.0},
        )

    blob = _blob(
        title=title,
        text=text,
        url=url,
        publisher=publisher,
        metadata=metadata,
    )
    scores: dict[str, float] = {}
    reason_map: dict[str, list[str]] = {}
    for content_type in _TYPE_SIGNALS:
        score, reasons = _score_type(content_type, blob, url)
        if score > 0:
            scores[content_type] = score
            reason_map[content_type] = reasons

    if not scores:
        return ClassificationResult(
            content_type=ContentType.NEWS.value,
            confidence=0.35,
            reasons=[
                'No strong genre signals found; defaulting to news for '
                'backwards compatibility.'
            ],
            scores={ContentType.NEWS.value: 0.35},
        )

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    winner, top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    # Softmax-ish confidence from relative score margin.
    confidence = min(0.95, 0.45 + (top / (top + second + 1.0)) * 0.5)
    if top >= 3:
        confidence = min(0.97, confidence + 0.1)
    return ClassificationResult(
        content_type=winner,
        confidence=confidence,
        reasons=reason_map.get(winner, [])[:5],
        scores=scores,
    )


def looks_like_word(blob: str, token: str) -> bool:
    return bool(re.search(rf'\b{re.escape(token)}\b', blob, flags=re.IGNORECASE))
