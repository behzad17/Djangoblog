from django.db.models import QuerySet

from community.models import CommunityCategory


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


def get_category_by_slug(slug: str) -> CommunityCategory:
    """Return an active category by slug."""
    return list_active_categories().get(slug=slug)


def category_exists(slug: str) -> bool:
    """Return whether any category exists for the slug."""
    return _category_queryset().filter(slug=slug).exists()
