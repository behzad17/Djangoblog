"""Related content selectors for cross-app recommendations."""

from __future__ import annotations

from typing import Any

from django.db.models import Q, QuerySet

from ads.config.blog_category_mapping import BLOG_TO_AD_CATEGORY_SLUGS
from ads.config.community_category_mapping import COMMUNITY_TO_AD_CATEGORY_SLUGS
from ads.models import Ad
from codestar.related.category_mapping import mapped_values_for_source
from codestar.related.sources import related_content_source
from codestar.related.text_matching import (
    extract_search_keywords,
    keyword_search_variants,
    score_token_overlap,
    tokenize_persian_text,
)
from ads.selectors.visibility import list_publicly_visible_pro_ads

_MIN_KEYWORD_SCORE = 2
_KEYWORD_CANDIDATE_LIMIT = 40
_MAX_KEYWORD_VARIANTS = 12


def get_related_ads(content: Any, *, limit: int = 3) -> list[Ad]:
    """
    Return contextually related, publicly visible Pro ads for a discussion or post.

    Accepts a Community ``Discussion``, Blog ``Post``, or ``RelatedContentSource``.

    Matching priority:
    1. Mapped ad categories for the content category
    2. Shared tags (skipped — not supported yet)
    3. Keyword overlap with ad titles
    4. Keyword overlap with ad category name/description
    """
    if limit <= 0:
        return []

    source = related_content_source(content)
    base_qs = list_publicly_visible_pro_ads()
    results: list[Ad] = []
    seen_ids: set[int] = set()

    mapped_slugs = mapped_values_for_source(
        source,
        community_map=COMMUNITY_TO_AD_CATEGORY_SLUGS,
        blog_map=BLOG_TO_AD_CATEGORY_SLUGS,
    )
    if mapped_slugs:
        for ad in base_qs.filter(category__slug__in=mapped_slugs)[:limit]:
            if ad.pk not in seen_ids:
                results.append(ad)
                seen_ids.add(ad.pk)

    if len(results) >= limit:
        return results[:limit]

    keywords = extract_search_keywords(source.title, source.body)
    if not keywords:
        return results[:limit]

    remaining = limit - len(results)
    title_matches = _keyword_matches(
        base_qs.exclude(pk__in=seen_ids),
        keywords,
        fields=('title',),
        weight=2,
        limit=remaining,
    )
    for ad in title_matches:
        if ad.pk not in seen_ids:
            results.append(ad)
            seen_ids.add(ad.pk)
        if len(results) >= limit:
            return results[:limit]

    remaining = limit - len(results)
    description_matches = _keyword_matches(
        base_qs.exclude(pk__in=seen_ids),
        keywords,
        fields=('category__name', 'category__description'),
        weight=1,
        limit=remaining,
    )
    for ad in description_matches:
        if ad.pk not in seen_ids:
            results.append(ad)
            seen_ids.add(ad.pk)
        if len(results) >= limit:
            break

    return results[:limit]


def _keyword_matches(
    queryset: QuerySet[Ad],
    keywords: list[str],
    *,
    fields: tuple[str, ...],
    weight: int,
    limit: int,
) -> list[Ad]:
    if limit <= 0 or not keywords:
        return []

    query = Q()
    variants_used = 0
    for keyword in keywords:
        for variant in keyword_search_variants(keyword):
            if variants_used >= _MAX_KEYWORD_VARIANTS:
                break
            for field in fields:
                query |= Q(**{f'{field}__icontains': variant})
            variants_used += 1

    if not query:
        return []

    candidates = list(queryset.filter(query)[:_KEYWORD_CANDIDATE_LIMIT])
    scored = [
        (ad, _score_ad(ad, keywords, fields=fields, weight=weight))
        for ad in candidates
    ]
    scored = [item for item in scored if item[1] >= _MIN_KEYWORD_SCORE]
    scored.sort(key=lambda item: (-item[1], -item[0].created_on.timestamp()))
    return [ad for ad, _score in scored[:limit]]


def _score_ad(
    ad: Ad,
    keywords: list[str],
    *,
    fields: tuple[str, ...],
    weight: int,
) -> int:
    haystacks: list[str] = []
    if 'title' in fields:
        haystacks.append(ad.title or '')
    if 'category__name' in fields and ad.category_id:
        haystacks.append(ad.category.name)
    if 'category__description' in fields and ad.category_id:
        haystacks.append(ad.category.description or '')

    haystack_tokens = []
    for haystack in haystacks:
        haystack_tokens.extend(tokenize_persian_text(haystack))

    return score_token_overlap(keywords, haystack_tokens, weight=weight)
