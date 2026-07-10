from django.db.models import QuerySet

from community.models import Reply


def _reply_queryset() -> QuerySet[Reply]:
    return Reply.objects.select_related('author', 'discussion', 'reviewed_by')


def list_replies(discussion) -> QuerySet[Reply]:
    """Return all replies for a discussion in chronological order."""
    return _reply_queryset().filter(discussion=discussion).order_by('created_on')


def list_public_replies(discussion) -> QuerySet[Reply]:
    """Return approved replies for a discussion in chronological order."""
    return (
        _reply_queryset()
        .filter(discussion=discussion, approved=True)
        .order_by('created_on')
    )


def count_public_replies(discussion) -> int:
    """Return the number of approved replies on a discussion."""
    return list_public_replies(discussion).count()


def list_pending_replies() -> QuerySet[Reply]:
    """Return replies awaiting moderation, newest first."""
    return (
        _reply_queryset()
        .filter(approved=False)
        .order_by('-created_on')
    )


def list_replies_by_author(user) -> QuerySet[Reply]:
    """Return approved replies authored by a user, newest first."""
    return (
        _reply_queryset()
        .filter(author=user, approved=True)
        .order_by('-created_on')
    )
