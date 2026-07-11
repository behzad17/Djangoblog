"""Related content selectors for expert recommendations."""

from __future__ import annotations

from typing import Any

from django.db.models import Q, QuerySet

from askme.models import Moderator
from codestar.related.category_mapping import mapped_values_for_source
from codestar.related.sources import RelatedContentSource, related_content_source
from codestar.related.text_matching import (
    extract_search_keywords,
    keyword_search_variants,
    normalize_persian_text,
    score_token_overlap,
    tokenize_persian_text,
)
from experts.config.blog_category_mapping import BLOG_TO_EXPERT_SPECIALTIES
from experts.config.community_category_mapping import COMMUNITY_TO_EXPERT_SPECIALTIES
from experts.config.specific_category_fallback import (
    BLOG_SPECIFIC_CATEGORY_FALLBACK,
    COMMUNITY_SPECIFIC_CATEGORY_FALLBACK,
)
from experts.selectors.visibility import list_publicly_visible_experts

# Stricter than ads/links: require topical keyword overlap, never pad to limit.
_MIN_EXPERT_TOTAL_SCORE = 2
_MIN_TITLE_SPECIALTY_KEYWORD_SCORE = 2
_CATEGORY_SPECIALTY_BONUS = 2
_KEYWORD_CANDIDATE_LIMIT = 40
_MAX_KEYWORD_VARIANTS = 12


def get_related_experts(content: Any, *, limit: int = 3) -> list[Moderator]:
    """
    Return precisely matched, publicly visible experts for a discussion or post.

    Accepts a Community ``Discussion``, Blog ``Post``, or ``RelatedContentSource``.

    Matching priority:
    1. Persian keyword overlap with expert title and specialty (primary)
    2. Shared tags (skipped — not supported yet)
    3. Mapped specialty terms (scoring bonus during keyword matching)
    4. Highly specific category fallback when no keywords can be extracted

    Returns fewer than ``limit`` results when only weak matches exist.
    """
    if limit <= 0:
        return []

    source = related_content_source(content)
    base_qs = list_publicly_visible_experts()
    keywords = extract_search_keywords(source.title, source.body)
    if not keywords:
        return _experts_for_specific_category_fallback(source, base_qs, limit=limit)

    specialty_terms = mapped_values_for_source(
        source,
        community_map=COMMUNITY_TO_EXPERT_SPECIALTIES,
        blog_map=BLOG_TO_EXPERT_SPECIALTIES,
    )

    candidates = _keyword_candidates(base_qs, keywords)
    scored: list[tuple[Moderator, int]] = []

    for expert in candidates:
        title_specialty_score = _score_expert(
            expert,
            keywords,
            fields=('expert_title', 'field_specialty'),
            weight=2,
        )
        if title_specialty_score < _MIN_TITLE_SPECIALTY_KEYWORD_SCORE:
            continue

        total_score = title_specialty_score
        total_score += _score_expert(
            expert,
            keywords,
            fields=('bio',),
            weight=1,
        )
        if specialty_terms and _matches_category_specialty(expert, specialty_terms):
            total_score += _CATEGORY_SPECIALTY_BONUS

        if total_score >= _MIN_EXPERT_TOTAL_SCORE:
            scored.append((expert, total_score))

    scored.sort(
        key=lambda item: (-item[1], item[0].expert_title, item[0].user.username),
    )
    return [expert for expert, _score in scored[:limit]]


def _specific_fallback_terms(source: RelatedContentSource) -> list[str]:
    slug = source.category_slug or ''
    if source.namespace == 'blog':
        return list(BLOG_SPECIFIC_CATEGORY_FALLBACK.get(slug, []))
    return list(COMMUNITY_SPECIFIC_CATEGORY_FALLBACK.get(slug, []))


def _experts_for_specific_category_fallback(
    source: RelatedContentSource,
    queryset: QuerySet[Moderator],
    *,
    limit: int,
) -> list[Moderator]:
    """Return experts for narrow category mappings when content has no keywords."""
    fallback_terms = _specific_fallback_terms(source)
    if not fallback_terms:
        return []

    query = Q()
    for term in fallback_terms:
        query |= Q(expert_title__icontains=term)
        query |= Q(field_specialty__icontains=term)

    candidates = list(queryset.filter(query)[:_KEYWORD_CANDIDATE_LIMIT])
    scored: list[tuple[Moderator, int]] = []

    for expert in candidates:
        match_count = sum(
            1
            for term in fallback_terms
            if _term_in_title_or_specialty(expert, term)
        )
        if match_count >= 1:
            scored.append((expert, match_count))

    scored.sort(
        key=lambda item: (-item[1], item[0].expert_title, item[0].user.username),
    )
    return [expert for expert, _score in scored[:limit]]


def _term_in_title_or_specialty(expert: Moderator, term: str) -> bool:
    normalized_term = normalize_persian_text(term)
    if not normalized_term:
        return False
    haystack = normalize_persian_text(
        f'{expert.expert_title or ""} {expert.field_specialty or ""}',
    )
    return normalized_term in haystack


def _keyword_candidates(
    queryset: QuerySet[Moderator],
    keywords: list[str],
) -> list[Moderator]:
    query = Q()
    variants_used = 0
    fields = ('expert_title', 'field_specialty', 'bio')

    for keyword in keywords:
        for variant in keyword_search_variants(keyword):
            if variants_used >= _MAX_KEYWORD_VARIANTS:
                break
            for field in fields:
                query |= Q(**{f'{field}__icontains': variant})
            variants_used += 1

    if not query:
        return []

    return list(queryset.filter(query)[:_KEYWORD_CANDIDATE_LIMIT])


def _matches_category_specialty(expert: Moderator, specialty_terms: list[str]) -> bool:
    haystack = normalize_persian_text(
        f'{expert.expert_title or ""} {expert.field_specialty or ""}',
    )
    return any(
        normalize_persian_text(term) in haystack
        for term in specialty_terms
        if term
    )


def _score_expert(
    expert: Moderator,
    keywords: list[str],
    *,
    fields: tuple[str, ...],
    weight: int,
) -> int:
    haystacks: list[str] = []
    if 'expert_title' in fields:
        haystacks.append(expert.expert_title or '')
    if 'field_specialty' in fields:
        haystacks.append(expert.field_specialty or '')
    if 'bio' in fields:
        haystacks.append(expert.bio or '')

    haystack_tokens = []
    for haystack in haystacks:
        haystack_tokens.extend(tokenize_persian_text(haystack))

    return score_token_overlap(keywords, haystack_tokens, weight=weight)
