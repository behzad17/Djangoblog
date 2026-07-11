from django.db.models import Count, Q, QuerySet

from community.models import CommunityCategory
from community.selectors.discussions import PUBLIC_DISCUSSION_STATUSES


def _category_queryset() -> QuerySet[CommunityCategory]:
    return CommunityCategory.objects.all()


def list_categories() -> QuerySet[CommunityCategory]:
    """Return all categories ordered for display."""
    return _category_queryset().order_by('display_order', 'name')


def list_active_categories() -> QuerySet[CommunityCategory]:
    """Return active categories ordered for public display."""
    return (
        _category_queryset()
        .filter(is_active=True)
        .order_by('display_order', 'name')
    )


def list_active_categories_with_discussion_counts() -> QuerySet[CommunityCategory]:
    """Return active categories annotated with public discussion counts."""
    public_discussions = Q(
        discussions__is_deleted=False,
        discussions__status__in=PUBLIC_DISCUSSION_STATUSES,
    )
    return list_active_categories().annotate(
        discussion_count=Count('discussions', filter=public_discussions),
    )


def get_category_by_slug(slug: str) -> CommunityCategory:
    """Return an active category by slug."""
    return list_active_categories().get(slug=slug)


def category_exists(slug: str) -> bool:
    """Return whether any category exists for the slug."""
    return _category_queryset().filter(slug=slug).exists()
