"""Writing style detection (heuristic)."""

from __future__ import annotations

from dataclasses import dataclass, field

from content_ai.editorial.content_types.constants import (
    WRITING_STYLE_LABELS,
    WritingStyle,
)
from content_ai.editorial.content_types.registry import get_profile, resolve_style


@dataclass(frozen=True, slots=True)
class StyleDetectionResult:
    style: str
    confidence: float
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            'style': self.style,
            'confidence': round(float(self.confidence), 3),
            'reasons': list(self.reasons),
        }


_STYLE_SIGNALS: dict[str, tuple[str, ...]] = {
    WritingStyle.EDUCATIONAL: (
        'guide',
        'how to',
        'steg',
        'learn',
        'tutorial',
        'آموزش',
        'راهنما',
    ),
    WritingStyle.OFFICIAL: (
        'pressmeddelande',
        'myndigheten',
        'förordning',
        'kungörelse',
        'official',
        'اطلاعیه',
        'بیانیه',
    ),
    WritingStyle.ANALYTICAL: (
        'analys',
        'analysis',
        'implication',
        'utredning',
        'تحلیل',
        'research',
    ),
    WritingStyle.HUMAN_INTEREST: (
        'portrait',
        'story',
        'community',
        'family',
        'زندگی',
        'داستان',
        'پرتره',
    ),
    WritingStyle.CONVERSATIONAL: (
        'intervju',
        'interview',
        'q&a',
        'tips',
        'مصاحبه',
    ),
    WritingStyle.NEUTRAL: (
        'neutral',
        'fact sheet',
        'backgrounder',
        'neutral ton',
    ),
    WritingStyle.JOURNALISTIC: (
        'nyheter',
        'news',
        'breaking',
        'reportage',
        'خبر',
    ),
}


def detect_writing_style(
    *,
    content_type: str = '',
    title: str = '',
    text: str = '',
    override: str | None = None,
) -> StyleDetectionResult:
    """Detect writing style from source cues, biased by content-type default."""
    if override:
        resolved = resolve_style(override, content_type=content_type)
        return StyleDetectionResult(
            style=resolved,
            confidence=1.0,
            reasons=['Editor override selected this writing style.'],
        )

    profile = get_profile(content_type)
    default_style = resolve_style(
        profile.default_style,
        content_type=profile.content_type,
    )
    blob = f'{title} {text[:2000]}'.lower()
    scores: dict[str, float] = {default_style: 0.6}
    reasons: dict[str, list[str]] = {
        default_style: [
            f'Default style for {profile.label} is '
            f'{WRITING_STYLE_LABELS.get(default_style, default_style)}.'
        ]
    }

    for style, tokens in _STYLE_SIGNALS.items():
        for token in tokens:
            if token in blob:
                scores[style] = scores.get(style, 0.0) + 1.0
                reasons.setdefault(style, []).append(
                    f'Matched style signal “{token}”.'
                )

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    winner, top = ranked[0]
    second = ranked[1][1] if len(ranked) > 1 else 0.0
    confidence = min(0.95, 0.5 + (top / (top + second + 1.0)) * 0.45)
    if top >= 2.5:
        confidence = min(0.97, confidence + 0.08)
    return StyleDetectionResult(
        style=winner,
        confidence=confidence,
        reasons=(reasons.get(winner) or [])[:4],
    )
