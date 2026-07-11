from django.db.models import QuerySet

from related_links.models import RelatedLink


def list_publicly_visible_links() -> QuerySet[RelatedLink]:
    """Return active links in active categories for public surfaces."""
    return (
        RelatedLink.objects.filter(
            is_active=True,
            category__is_active=True,
        )
        .select_related('category', 'resource_type')
        .order_by('order', '-created_on')
    )
