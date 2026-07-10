from django.db import connections
from django.db.models import Max

from community.models import Discussion, Reply


def recalculate_discussion_stats(discussion: Discussion) -> Discussion:
    """
    Recompute denormalized reply_count and last_activity_at for a discussion.

    Must be called inside transaction.atomic() when concurrent writes are possible.
    Locks the discussion row when a database transaction is active.
    """
    connection = connections[Discussion.objects.db]
    queryset = Discussion.objects.filter(pk=discussion.pk)
    if connection.in_atomic_block:
        discussion = queryset.select_for_update().get(pk=discussion.pk)
    else:
        discussion = queryset.get(pk=discussion.pk)

    approved_replies = Reply.objects.filter(
        discussion=discussion,
        approved=True,
    )
    reply_count = approved_replies.count()
    last_reply_at = approved_replies.aggregate(latest=Max('created_on'))['latest']
    last_activity_at = last_reply_at or discussion.created_on

    discussion.reply_count = reply_count
    discussion.last_activity_at = last_activity_at
    discussion.save(update_fields=['reply_count', 'last_activity_at', 'updated_on'])
    return discussion
