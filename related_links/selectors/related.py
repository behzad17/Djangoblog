"""Related content selectors for useful link recommendations."""

from django.db.models import Q, QuerySet

from codestar.related.text_matching import (
    extract_search_keywords,
    keyword_search_variants,
    score_token_overlap,
    tokenize_persian_text,
)
from community.models import Discussion
from related_links.config.community_category_mapping import (
    useful_link_category_slugs_for_community_category,
)
from related_links.models import RelatedLink
from related_links.selectors.visibility import list_publicly_visible_links

_MIN_KEYWORD_SCORE = 2
_KEYWORD_CANDIDATE_LIMIT = 40
_MAX_KEYWORD_VARIANTS = 12


def get_related_links(discussion: Discussion, *, limit: int = 3) -> list[RelatedLink]:
    """
    Return contextually related, publicly visible useful links for a discussion.

    Matching priority:
    1. Mapped useful link categories for the discussion category
    2. Shared tags (skipped — not supported yet)
    3. Persian keyword overlap with link titles and short descriptions
    4. Keyword overlap with link descriptions and category text
    """
    if limit <= 0:
        return []

    base_qs = list_publicly_visible_links()
    results: list[RelatedLink] = []
    seen_ids: set[int] = set()

    category = getattr(discussion, 'category', None)
    if category is not None:
        mapped_slugs = useful_link_category_slugs_for_community_category(
            category.slug,
        )
        if mapped_slugs:
            for link in base_qs.filter(category__slug__in=mapped_slugs)[:limit]:
                if link.pk not in seen_ids:
                    results.append(link)
                    seen_ids.add(link.pk)

    if len(results) >= limit:
        return results[:limit]

    keywords = extract_search_keywords(discussion.title, discussion.body)
    if not keywords:
        return results[:limit]

    remaining = limit - len(results)
    title_matches = _keyword_matches(
        base_qs.exclude(pk__in=seen_ids),
        keywords,
        fields=('title', 'short_description'),
        weight=2,
        limit=remaining,
    )
    for link in title_matches:
        if link.pk not in seen_ids:
            results.append(link)
            seen_ids.add(link.pk)
        if len(results) >= limit:
            return results[:limit]

    remaining = limit - len(results)
    description_matches = _keyword_matches(
        base_qs.exclude(pk__in=seen_ids),
        keywords,
        fields=(
            'description',
            'source_name',
            'category__name_fa',
            'category__name_en',
            'category__description',
        ),
        weight=1,
        limit=remaining,
    )
    for link in description_matches:
        if link.pk not in seen_ids:
            results.append(link)
            seen_ids.add(link.pk)
        if len(results) >= limit:
            break

    return results[:limit]


def _keyword_matches(
    queryset: QuerySet[RelatedLink],
    keywords: list[str],
    *,
    fields: tuple[str, ...],
    weight: int,
    limit: int,
) -> list[RelatedLink]:
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
        (link, _score_link(link, keywords, fields=fields, weight=weight))
        for link in candidates
    ]
    scored = [item for item in scored if item[1] >= _MIN_KEYWORD_SCORE]
    scored.sort(key=lambda item: (-item[1], item[0].order, -item[0].created_on.timestamp()))
    return [link for link, _score in scored[:limit]]


def _score_link(
    link: RelatedLink,
    keywords: list[str],
    *,
    fields: tuple[str, ...],
    weight: int,
) -> int:
    haystacks: list[str] = []
    if 'title' in fields:
        haystacks.append(link.title or '')
    if 'short_description' in fields:
        haystacks.append(link.short_description or '')
    if 'description' in fields:
        haystacks.append(link.description or '')
    if 'source_name' in fields:
        haystacks.append(link.source_name or '')
    if 'category__name_fa' in fields and link.category_id:
        haystacks.append(link.category.name_fa)
    if 'category__name_en' in fields and link.category_id:
        haystacks.append(link.category.name_en)
    if 'category__description' in fields and link.category_id:
        haystacks.append(link.category.description or '')

    haystack_tokens = []
    for haystack in haystacks:
        haystack_tokens.extend(tokenize_persian_text(haystack))

    return score_token_overlap(keywords, haystack_tokens, weight=weight)
