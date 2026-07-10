from django.db import transaction
from django.utils import timezone

from community.constants import DiscussionStatus, ModerationReason
from community.exceptions import (
    DiscussionClosedError,
    DiscussionDeletedError,
    InvalidDiscussionStateError,
    ReplyModerationError,
    UnauthorizedAuthorError,
    ValidationError,
)
from community.models import Discussion, Reply
from community.services.counters import recalculate_discussion_stats
from community.services.moderation import should_auto_approve_reply


def _validate_non_empty(value: str, field_name: str) -> str:
    cleaned = (value or '').strip()
    if not cleaned:
        raise ValidationError(f'{field_name} must not be empty.')
    return cleaned


def _validate_reply_target(discussion: Discussion) -> None:
    if discussion.is_deleted:
        raise DiscussionDeletedError(
            f'Discussion "{discussion.slug}" has been deleted.'
        )
    if discussion.status == DiscussionStatus.HIDDEN:
        raise InvalidDiscussionStateError(
            f'Discussion "{discussion.slug}" is not accepting replies.'
        )
    if discussion.status == DiscussionStatus.CLOSED:
        raise DiscussionClosedError(
            f'Discussion "{discussion.slug}" is closed.'
        )
    if discussion.status != DiscussionStatus.OPEN:
        raise InvalidDiscussionStateError(
            f'Discussion "{discussion.slug}" is not accepting replies.'
        )


def _apply_moderation_decision(reply: Reply, *, approved: bool, reason: str | None) -> None:
    reply.approved = approved
    reply.moderation_reason = None if approved else reason


def create_reply(*, discussion: Discussion, author, body: str) -> Reply:
    """Create a reply and refresh discussion stats when auto-approved."""
    if author is None or not getattr(author, 'is_authenticated', False):
        raise ValidationError('author must be an authenticated user.')

    _validate_reply_target(discussion)
    body = _validate_non_empty(body, 'body')
    approved, moderation_reason = should_auto_approve_reply(author, body)

    with transaction.atomic():
        reply = Reply.objects.create(
            discussion=discussion,
            author=author,
            body=body,
            approved=approved,
            moderation_reason=moderation_reason,
        )
        if approved:
            recalculate_discussion_stats(discussion)

    return reply


def edit_reply(*, reply: Reply, author, body: str) -> Reply:
    """Edit a reply and re-evaluate moderation when content changes."""
    if reply.author_id != getattr(author, 'pk', None):
        raise UnauthorizedAuthorError('Only the reply author may edit this reply.')

    _validate_reply_target(reply.discussion)
    body = _validate_non_empty(body, 'body')
    approved, moderation_reason = should_auto_approve_reply(author, body)
    was_approved = reply.approved

    with transaction.atomic():
        reply.body = body
        _apply_moderation_decision(reply, approved=approved, reason=moderation_reason)
        reply.save(update_fields=['body', 'approved', 'moderation_reason', 'updated_on'])
        if was_approved or approved:
            recalculate_discussion_stats(reply.discussion)

    return reply


def approve_reply(*, reply: Reply, reviewer) -> Reply:
    """Approve a pending reply and refresh discussion stats."""
    if reply.approved:
        return reply

    now = timezone.now()
    with transaction.atomic():
        reply.approved = True
        reply.moderation_reason = None
        reply.reviewed_by = reviewer
        reply.reviewed_at = now
        reply.save(
            update_fields=[
                'approved',
                'moderation_reason',
                'reviewed_by',
                'reviewed_at',
                'updated_on',
            ],
        )
        recalculate_discussion_stats(reply.discussion)

    return reply


def reject_reply(
    *,
    reply: Reply,
    reviewer,
    reason: str = ModerationReason.MANUAL_REVIEW,
) -> Reply:
    """Reject or unapprove a reply and refresh discussion stats."""
    valid_reasons = {choice.value for choice in ModerationReason}
    if reason not in valid_reasons:
        raise ReplyModerationError(f'Invalid moderation reason: {reason}')

    now = timezone.now()

    with transaction.atomic():
        reply.approved = False
        reply.moderation_reason = reason
        reply.reviewed_by = reviewer
        reply.reviewed_at = now
        reply.save(
            update_fields=[
                'approved',
                'moderation_reason',
                'reviewed_by',
                'reviewed_at',
                'updated_on',
            ],
        )
        recalculate_discussion_stats(reply.discussion)

    return reply
