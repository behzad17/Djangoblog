"""Related content selectors for expert recommendations."""

from django.db.models import Q, QuerySet

from ads.selectors.text_matching import (
    extract_search_keywords,
    keyword_search_variants,
    score_token_overlap,
    tokenize_persian_text,
)
from askme.models import Moderator
from community.models import Discussion
from experts.config.community_category_mapping import (
    expert_specialties_for_community_category,
)
from experts.selectors.visibility import list_publicly_visible_experts

_MIN_KEYWORD_SCORE = 2
_KEYWORD_CANDIDATE_LIMIT = 40
_MAX_KEYWORD_VARIANTS = 12


def get_related_experts(discussion: Discussion, *, limit: int = 3) -> list[Moderator]:
    """
    Return contextually related, publicly visible experts for a discussion.

    Matching priority:
    1. Mapped specialty/expertise terms for the discussion category
    2. Shared tags (skipped — not supported yet)
    3. Persian keyword overlap with expert title and specialty
    4. Keyword overlap with expert bio/description
    """
    if limit <= 0:
        return []

    base_qs = list_publicly_visible_experts()
    results: list[Moderator] = []
    seen_ids: set[int] = set()

    category = getattr(discussion, 'category', None)
    if category is not None:
        specialty_terms = expert_specialties_for_community_category(category.slug)
        if specialty_terms:
            specialty_query = Q()
            for term in specialty_terms:
                specialty_query |= Q(field_specialty__icontains=term)
                specialty_query |= Q(expert_title__icontains=term)

            for expert in base_qs.filter(specialty_query)[:limit]:
                if expert.pk not in seen_ids:
                    results.append(expert)
                    seen_ids.add(expert.pk)

    if len(results) >= limit:
        return results[:limit]

    keywords = extract_search_keywords(discussion.title, discussion.body)
    if not keywords:
        return results[:limit]

    remaining = limit - len(results)
    title_matches = _keyword_matches(
        base_qs.exclude(pk__in=seen_ids),
        keywords,
        fields=('expert_title', 'field_specialty'),
        weight=2,
        limit=remaining,
    )
    for expert in title_matches:
        if expert.pk not in seen_ids:
            results.append(expert)
            seen_ids.add(expert.pk)
        if len(results) >= limit:
            return results[:limit]

    remaining = limit - len(results)
    description_matches = _keyword_matches(
        base_qs.exclude(pk__in=seen_ids),
        keywords,
        fields=('bio', 'expert_title', 'field_specialty'),
        weight=1,
        limit=remaining,
    )
    for expert in description_matches:
        if expert.pk not in seen_ids:
            results.append(expert)
            seen_ids.add(expert.pk)
        if len(results) >= limit:
            break

    return results[:limit]


def _keyword_matches(
    queryset: QuerySet[Moderator],
    keywords: list[str],
    *,
    fields: tuple[str, ...],
    weight: int,
    limit: int,
) -> list[Moderator]:
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
        (expert, _score_expert(expert, keywords, fields=fields, weight=weight))
        for expert in candidates
    ]
    scored = [item for item in scored if item[1] >= _MIN_KEYWORD_SCORE]
    scored.sort(key=lambda item: (-item[1], item[0].expert_title))
    return [expert for expert, _score in scored[:limit]]


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
