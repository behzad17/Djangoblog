from django.conf import settings
from django.db import connection
from django.db.models import Q, QuerySet
from django.db.models.functions import Coalesce

from community.models import Discussion
from community.selectors.discussions import _public_discussions_queryset


def search_discussions(
    query: str,
    *,
    category=None,
) -> QuerySet[Discussion]:
    """Search public discussions by title and body."""
    queryset = _public_discussions_queryset()
    cleaned_query = (query or '').strip()

    if category is not None:
        queryset = queryset.filter(category=category)

    if not cleaned_query:
        return queryset.order_by('-last_activity_at')

    if connection.vendor == 'postgresql':
        from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector

        search_config = getattr(settings, 'COMMUNITY_SEARCH_CONFIG', 'simple')
        min_rank = getattr(settings, 'COMMUNITY_SEARCH_MIN_RANK', 0.01)
        vector = (
            SearchVector('title', weight='A', config=search_config)
            + SearchVector('body', weight='B', config=search_config)
        )
        search_query = SearchQuery(cleaned_query, config=search_config)
        queryset = (
            queryset.annotate(
                rank=Coalesce(SearchRank(vector, search_query), 0.0),
            )
            .filter(rank__gte=min_rank)
            .order_by('-rank', '-last_activity_at')
        )
        if queryset.exists():
            return queryset

    return (
        queryset.filter(
            Q(title__icontains=cleaned_query)
            | Q(body__icontains=cleaned_query),
        )
        .order_by('-last_activity_at')
    )
