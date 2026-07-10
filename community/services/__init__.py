"""Community write operations and business logic."""

from community.services.counters import recalculate_discussion_stats
from community.services.discussions import (
    close_discussion,
    create_discussion,
    reopen_discussion,
    restore_discussion,
    soft_delete_discussion,
    update_discussion,
)
from community.services.moderation import should_auto_approve_reply
from community.services.replies import (
    approve_reply,
    create_reply,
    edit_reply,
    reject_reply,
)

__all__ = [
    'approve_reply',
    'close_discussion',
    'create_discussion',
    'create_reply',
    'edit_reply',
    'recalculate_discussion_stats',
    'reject_reply',
    'reopen_discussion',
    'restore_discussion',
    'should_auto_approve_reply',
    'soft_delete_discussion',
    'update_discussion',
]

# Extension point: structured audit/logging hooks may wrap service calls here.
