"""Intelligent Blog category recommendation from imported article content.

Scores every live Blog category using the full article text plus editorial
signals. New categories are supported automatically via name/slug/description
matching — no hardcoded category IDs.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

AUTO_SELECT_THRESHOLD = 0.90
WEAK_MATCH_THRESHOLD = 0.70

# Optional semantic enrichment keyed by slug tokens / known taxonomy slugs.
# New categories still work without entries here (name/slug/description matching).
TOPIC_HINTS: dict[str, tuple[str, ...]] = {
    'careers-economy': (
        'tax',
        'skatt',
        'skatteverket',
        'economy',
        'ekonom',
        'jobb',
        'arbetsmarknad',
        'salary',
        'lön',
        'مالیات',
        'اقتصاد',
        'بازار کار',
        'اشتغال',
        'declaration',
        'deklaration',
        'inkomst',
    ),
    'life-in-sweden': (
        'sweden',
        'sverige',
        'bostad',
        'housing',
        'living',
        'guide',
        'زندگی',
        'سوئد',
        'مسکن',
        'bankid',
        'personnummer',
        'försäkring',
        'vardag',
    ),
    'law-integration': (
        'law',
        'lag',
        'migration',
        'migrationsverket',
        'asyl',
        'integration',
        'citizenship',
        'medborgarskap',
        'قانون',
        'ادغام',
        'مهاجرت',
        'visa',
        'uppehållstillstånd',
        'regel',
        'förordning',
    ),
    'skills-learning': (
        'utbildning',
        'education',
        'course',
        'kurs',
        'sfi',
        'skill',
        'learn',
        'آموزش',
        'مهارت',
        'university',
        'universitet',
    ),
    'events-announcements': (
        'event',
        'evenemang',
        'announcement',
        'meddelande',
        'seminar',
        'festival',
        'رویداد',
        'اطلاعیه',
        'registration',
        'anmälan',
    ),
    'public-services': (
        'myndighet',
        'agency',
        'service',
        'vård',
        'healthcare',
        'försäkringskassan',
        'kommun',
        'خدمات',
        'عمومی',
        'hospital',
        'sjukhus',
    ),
    'stories-experiences': (
        'story',
        'berättelse',
        'experience',
        'portrait',
        'داستان',
        'تجربه',
        'interview',
        'intervju',
    ),
    'community-engagement': (
        'community',
        'diaspora',
        'volunteer',
        'förening',
        'جامعه',
        'مشارکت',
        'ngo',
    ),
    'platform-updates': (
        'news',
        'nyheter',
        'update',
        'breaking',
        'تازه‌',
        'خبر',
    ),
    'photo-gallery': (
        'photo',
        'gallery',
        'image',
        'عکس',
        'گالری',
    ),
    'guide-questions': (
        'faq',
        'question',
        'پرسش',
        'راهنما',
        'how to',
        'hur man',
    ),
}

CONTENT_TYPE_BOOSTS: dict[str, tuple[str, ...]] = {
    'guide': ('life-in-sweden', 'skills-learning', 'guide-questions', 'public-services'),
    'how_to': ('life-in-sweden', 'skills-learning', 'guide-questions'),
    'announcement': ('events-announcements', 'platform-updates'),
    'press_release': ('events-announcements', 'platform-updates', 'public-services'),
    'event': ('events-announcements',),
    'interview': ('stories-experiences', 'community-engagement'),
    'feature': ('stories-experiences', 'community-engagement'),
    'community_story': ('community-engagement', 'stories-experiences'),
    'faq': ('guide-questions', 'public-services', 'life-in-sweden'),
    'analysis': ('careers-economy', 'law-integration', 'platform-updates'),
    'report': ('careers-economy', 'law-integration', 'public-services'),
    'news': ('platform-updates',),
}

KNOWN_ENTITIES: dict[str, tuple[str, ...]] = {
    'skatteverket': ('careers-economy', 'public-services'),
    'migrationsverket': ('law-integration', 'public-services'),
    'försäkringskassan': ('public-services', 'life-in-sweden'),
    'arbetsförmedlingen': ('careers-economy', 'public-services'),
    'skolverket': ('skills-learning', 'public-services'),
    'socialstyrelsen': ('public-services',),
    'polisen': ('law-integration', 'public-services'),
    'regeringen': ('law-integration', 'platform-updates'),
    'riksdag': ('law-integration', 'platform-updates'),
    'bankid': ('life-in-sweden', 'public-services'),
    'tax': ('careers-economy',),
    'declaration': ('careers-economy',),
    'deklaration': ('careers-economy',),
}


@dataclass(frozen=True, slots=True)
class CategoryCandidate:
    slug: str
    name: str
    confidence: float
    matched_signals: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            'slug': self.slug,
            'name': self.name,
            'confidence': round(float(self.confidence), 3),
            'confidence_pct': int(round(float(self.confidence) * 100)),
            'matched_signals': list(self.matched_signals),
        }


@dataclass(frozen=True, slots=True)
class CategoryRecommendation:
    selected: CategoryCandidate | None
    candidates: list[CategoryCandidate]
    entities: list[str]
    reasons: list[str]
    auto_selected: bool
    needs_review: bool
    weak_match: bool
    message: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'selected': self.selected.to_dict() if self.selected else None,
            'candidates': [item.to_dict() for item in self.candidates],
            'entities': list(self.entities),
            'reasons': list(self.reasons),
            'auto_selected': self.auto_selected,
            'needs_review': self.needs_review,
            'weak_match': self.weak_match,
            'message': self.message,
        }


def _normalise_blob(*parts: str) -> str:
    return ' '.join(part or '' for part in parts).lower()


def _tokenize_name(name: str) -> set[str]:
    raw = (name or '').strip().lower()
    if not raw:
        return set()
    parts = re.split(r'[\s|/,&+_\-–—]+', raw)
    return {part for part in parts if len(part) >= 2}


def _slug_tokens(slug: str) -> set[str]:
    return {part for part in (slug or '').lower().split('-') if len(part) >= 2}


def detect_entities(text: str) -> list[str]:
    """Lightweight entity hints from known agencies and capitalised tokens."""
    blob = text or ''
    found: list[str] = []
    lowered = blob.lower()
    for key in KNOWN_ENTITIES:
        if key in lowered:
            label = key[:1].upper() + key[1:]
            if key == 'skatteverket':
                label = 'Skatteverket'
            elif key == 'migrationsverket':
                label = 'Migrationsverket'
            elif key == 'försäkringskassan':
                label = 'Försäkringskassan'
            elif key == 'arbetsförmedlingen':
                label = 'Arbetsförmedlingen'
            elif key == 'bankid':
                label = 'BankID'
            if label not in found:
                found.append(label)
    for match in re.findall(r'\b([A-ZÅÄÖ][a-zåäö]{3,})\b', blob):
        if match not in found and match.lower() not in {
            'this', 'that', 'with', 'from', 'sweden', 'iran',
        }:
            found.append(match)
        if len(found) >= 12:
            break
    return found[:10]


def _load_categories(categories: Iterable[Any] | None = None) -> list[dict[str, str]]:
    if categories is not None:
        payload = []
        for item in categories:
            if isinstance(item, dict):
                payload.append(
                    {
                        'slug': (item.get('slug') or '').strip(),
                        'name': (item.get('name') or '').strip(),
                        'description': (item.get('description') or '').strip(),
                    }
                )
            else:
                payload.append(
                    {
                        'slug': getattr(item, 'slug', '') or '',
                        'name': getattr(item, 'name', '') or '',
                        'description': getattr(item, 'description', '') or '',
                    }
                )
        return [item for item in payload if item['slug'] or item['name']]
    try:
        from blog.models import Category

        return [
            {
                'slug': category.slug,
                'name': category.name,
                'description': category.description or '',
            }
            for category in Category.objects.all().order_by(
                'display_order', 'name'
            )
        ]
    except Exception:  # noqa: BLE001 — allow SimpleTestCase / pre-migrate
        return []


def _fallback_category(categories: list[dict[str, str]]) -> dict[str, str] | None:
    preferences = (
        'platform-updates',
        'news',
        'general',
        'general-news',
    )
    by_slug = {item['slug']: item for item in categories if item.get('slug')}
    for slug in preferences:
        if slug in by_slug:
            return by_slug[slug]
    for item in categories:
        name = (item.get('name') or '').lower()
        if 'تازه‌' in name or 'news' in name or 'general' in name:
            return item
    return categories[0] if categories else None


def _category_signals(category: dict[str, str]) -> set[str]:
    signals = set()
    signals |= _tokenize_name(category.get('name') or '')
    signals |= _slug_tokens(category.get('slug') or '')
    signals |= _tokenize_name(category.get('description') or '')
    slug = category.get('slug') or ''
    for key, hints in TOPIC_HINTS.items():
        if slug == key or key in slug:
            signals |= {hint.lower() for hint in hints}
    # Also attach hints when slug tokens overlap hint keys.
    for token in _slug_tokens(slug):
        for key, hints in TOPIC_HINTS.items():
            if token in key or token in {h.split()[0] for h in hints if ' ' not in h}:
                signals |= {hint.lower() for hint in hints}
    return {signal for signal in signals if signal}


def recommend_category(
    *,
    headline: str = '',
    source_title: str = '',
    body: str = '',
    content_type: str = '',
    goal: str = '',
    style: str = '',
    publisher: str = '',
    categories: Iterable[Any] | None = None,
) -> CategoryRecommendation:
    """Recommend a Blog category from full article content and editorial signals."""
    catalogue = _load_categories(categories)
    if not catalogue:
        return CategoryRecommendation(
            selected=None,
            candidates=[],
            entities=[],
            reasons=['No Blog categories available for recommendation.'],
            auto_selected=False,
            needs_review=True,
            weak_match=True,
            message='No strong category match found.',
        )
    article_body = (body or '').strip()
    # Never classify from URL alone — require article text.
    if not article_body and not (headline or '').strip() and not (source_title or '').strip():
        fallback = _fallback_category(catalogue)
        selected = None
        if fallback:
            selected = CategoryCandidate(
                slug=fallback['slug'],
                name=fallback['name'],
                confidence=0.35,
                matched_signals=['Insufficient article text for category matching.'],
            )
        return CategoryRecommendation(
            selected=selected,
            candidates=[selected] if selected else [],
            entities=[],
            reasons=['No article text available for category recommendation.'],
            auto_selected=False,
            needs_review=True,
            weak_match=True,
            message='No strong category match found.',
        )

    blob = _normalise_blob(
        headline,
        source_title,
        article_body,
        publisher,
        content_type,
        goal,
        style,
    )
    entities = detect_entities(
        '\n'.join(part for part in (headline, source_title, article_body, publisher) if part)
    )
    entity_blob = ' '.join(entities).lower()

    scored: list[tuple[float, list[str], dict[str, str]]] = []
    for category in catalogue:
        score = 0.0
        matched: list[str] = []
        for signal in _category_signals(category):
            if signal and signal in blob:
                weight = 1.4 if len(signal) >= 6 else 1.0
                score += weight
                matched.append(signal)
        slug = category.get('slug') or ''
        for entity_key, boost_slugs in KNOWN_ENTITIES.items():
            if entity_key in blob or entity_key in entity_blob:
                if slug in boost_slugs or any(token in slug for token in boost_slugs):
                    score += 2.0
                    matched.append(entity_key)
        for boost_slug in CONTENT_TYPE_BOOSTS.get(content_type or '', ()):
            if slug == boost_slug or boost_slug in slug:
                score += 1.25
                matched.append(f'content_type:{content_type}')
        if goal == 'teach' and any(
            token in slug for token in ('life', 'skill', 'guide', 'learning')
        ):
            score += 0.75
            matched.append('goal:teach')
        if goal == 'announce' and any(
            token in slug for token in ('event', 'announce', 'platform')
        ):
            score += 0.75
            matched.append('goal:announce')
        # Prefer categories that match Persian/English name fragments strongly.
        name_tokens = _tokenize_name(category.get('name') or '')
        strong_name_hits = sum(1 for token in name_tokens if token in blob and len(token) >= 3)
        if strong_name_hits:
            score += strong_name_hits * 1.5
        scored.append((score, matched[:8], category))

    scored.sort(key=lambda item: item[0], reverse=True)
    if not scored or scored[0][0] <= 0:
        fallback = _fallback_category(catalogue)
        selected = None
        if fallback:
            selected = CategoryCandidate(
                slug=fallback['slug'],
                name=fallback['name'],
                confidence=0.4,
                matched_signals=['Fallback general news category.'],
            )
        return CategoryRecommendation(
            selected=selected,
            candidates=[selected] if selected else [],
            entities=entities,
            reasons=['No strong topical signals found in the article body.'],
            auto_selected=False,
            needs_review=True,
            weak_match=True,
            message='No strong category match found.',
        )

    top_score = scored[0][0]
    second = scored[1][0] if len(scored) > 1 else 0.0
    candidates: list[CategoryCandidate] = []
    for score, matched, category in scored[:3]:
        # Relative confidence with margin vs runner-up.
        confidence = min(
            0.99,
            0.45 + (score / (top_score + second + 1.0)) * 0.5 + min(score, 6) * 0.04,
        )
        if score == top_score and score >= 4:
            confidence = max(confidence, 0.91)
        if score == top_score and score >= 6:
            confidence = max(confidence, 0.95)
        if score < top_score:
            confidence = min(confidence, confidence * (score / top_score))
        candidates.append(
            CategoryCandidate(
                slug=category['slug'],
                name=category['name'],
                confidence=confidence,
                matched_signals=matched,
            )
        )

    winner = candidates[0]
    weak_match = winner.confidence < WEAK_MATCH_THRESHOLD
    if weak_match:
        fallback = _fallback_category(catalogue)
        if fallback:
            winner = CategoryCandidate(
                slug=fallback['slug'],
                name=fallback['name'],
                confidence=max(winner.confidence, 0.4),
                matched_signals=['Fallback general news category.'],
            )
            # Keep topical candidates visible, but selected is fallback.
            if not any(item.slug == winner.slug for item in candidates):
                candidates = [winner, *candidates][:3]
            else:
                candidates = [winner] + [
                    item for item in candidates if item.slug != winner.slug
                ][:2]
        message = 'No strong category match found.'
        auto_selected = False
        needs_review = True
    elif winner.confidence >= AUTO_SELECT_THRESHOLD:
        message = (
            f'Auto-selected category “{winner.name}” '
            f'({int(round(winner.confidence * 100))}%).'
        )
        auto_selected = True
        needs_review = False
    else:
        message = 'Please review the suggested category.'
        auto_selected = False
        needs_review = True

    reasons = [
        f'Matched category: {winner.name}',
        f'Confidence: {int(round(winner.confidence * 100))}%',
    ]
    if entities:
        reasons.insert(0, 'Detected entities: ' + ', '.join(entities[:6]))
    if winner.matched_signals:
        reasons.append(
            'Signals: ' + ', '.join(winner.matched_signals[:6])
        )

    return CategoryRecommendation(
        selected=winner,
        candidates=candidates,
        entities=entities,
        reasons=reasons,
        auto_selected=auto_selected,
        needs_review=needs_review,
        weak_match=weak_match,
        message=message,
    )


def list_blog_categories_for_ui() -> list[dict[str, str]]:
    """Return Blog categories for workspace selects."""
    try:
        from blog.models import Category

        return [
            {'slug': category.slug, 'name': category.name}
            for category in Category.objects.all().order_by(
                'display_order', 'name'
            )
        ]
    except Exception:  # noqa: BLE001 — workspace may boot before migrate
        return []
