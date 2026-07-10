from django.db.models import QuerySet

from community.constants import DiscussionStatus
from community.models import Discussion


PUBLIC_DISCUSSION_STATUSES = (
    DiscussionStatus.OPEN,
    DiscussionStatus.CLOSED,
)


def _public_discussions_queryset() -> QuerySet[Discussion]:
    return (
        Discussion.objects.filter(
            is_deleted=False,
            status__in=PUBLIC_DISCUSSION_STATUSES,
        )
        .select_related('author', 'category')
    )


def list_discussions() -> QuerySet[Discussion]:
    """Return all public discussions ordered by most recent activity."""
    return _public_discussions_queryset().order_by('-last_activity_at')


def list_latest_discussions() -> QuerySet[Discussion]:
    """Return all public discussions ordered by creation date."""
    return _public_discussions_queryset().order_by('-created_on')


def list_active_discussions() -> QuerySet[Discussion]:
    """Return public discussions with recent activity first."""
    return list_discussions()


def list_open_discussions() -> QuerySet[Discussion]:
    """Return public open discussions ordered by recent activity."""
    return (
        _public_discussions_queryset()
        .filter(status=DiscussionStatus.OPEN)
        .order_by('-last_activity_at')
    )


def list_closed_discussions() -> QuerySet[Discussion]:
    """Return public closed discussions ordered by recent activity."""
    return (
        _public_discussions_queryset()
        .filter(status=DiscussionStatus.CLOSED)
        .order_by('-last_activity_at')
    )


def list_discussions_by_category(category) -> QuerySet[Discussion]:
    """Return public discussions for a category ordered by recent activity."""
    return (
        _public_discussions_queryset()
        .filter(category=category)
        .order_by('-last_activity_at')
    )


def get_discussion_by_slug(slug: str) -> Discussion:
    """Return a single public discussion by slug."""
    return _public_discussions_queryset().get(slug=slug)


def list_discussions_by_author(user) -> QuerySet[Discussion]:
    """Return public discussions authored by a user."""
    return (
        _public_discussions_queryset()
        .filter(author=user)
        .order_by('-created_on')
    )


def discussion_exists(slug: str) -> bool:
    """Return whether a public discussion exists for the slug."""
    return _public_discussions_queryset().filter(slug=slug).exists()
