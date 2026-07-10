from django.db import IntegrityError, transaction
from django.utils import timezone

from blog.utils import generate_slug_from_persian
from community.constants import DiscussionStatus
from community.exceptions import (
    DiscussionDeletedError,
    InactiveCategoryError,
    InvalidDiscussionStateError,
    ValidationError,
)
from community.models import CommunityCategory, Discussion


def _validate_non_empty(value: str, field_name: str) -> str:
    cleaned = (value or '').strip()
    if not cleaned:
        raise ValidationError(f'{field_name} must not be empty.')
    return cleaned


def _validate_category(category: CommunityCategory) -> None:
    if not category.is_active:
        raise InactiveCategoryError(
            f'Category "{category.name}" is inactive and cannot be used.'
        )


def _validate_discussion_not_deleted(discussion: Discussion) -> None:
    if discussion.is_deleted:
        raise DiscussionDeletedError(
            f'Discussion "{discussion.slug}" has been deleted.'
        )


def _generate_unique_discussion_slug(title: str) -> str:
    base_slug = generate_slug_from_persian(title)
    if not base_slug:
        base_slug = f'discussion-{timezone.now().strftime("%Y%m%d%H%M%S")}'

    slug = base_slug
    counter = 2
    while Discussion.objects.filter(slug=slug).exists():
        slug = f'{base_slug}-{counter}'
        counter += 1
    return slug


def create_discussion(*, author, category: CommunityCategory, title: str, body: str) -> Discussion:
    """Create a new discussion with slug generation and initial counters."""
    _validate_category(category)
    title = _validate_non_empty(title, 'title')
    body = _validate_non_empty(body, 'body')

    now = timezone.now()

    with transaction.atomic():
        last_error = None
        for _ in range(5):
            slug = _generate_unique_discussion_slug(title)
            try:
                discussion = Discussion.objects.create(
                    author=author,
                    category=category,
                    title=title,
                    slug=slug,
                    body=body,
                    status=DiscussionStatus.OPEN,
                    reply_count=0,
                    last_activity_at=now,
                )
                return discussion
            except IntegrityError as exc:
                last_error = exc
        raise ValidationError(
            'Unable to create discussion due to slug conflict.'
        ) from last_error


def update_discussion(
    discussion: Discussion,
    *,
    title: str | None = None,
    body: str | None = None,
    category: CommunityCategory | None = None,
) -> Discussion:
    """Update editable discussion fields. Slugs are immutable after creation."""
    _validate_discussion_not_deleted(discussion)

    update_fields = ['updated_on']

    if title is not None:
        discussion.title = _validate_non_empty(title, 'title')
        update_fields.append('title')

    if body is not None:
        discussion.body = _validate_non_empty(body, 'body')
        update_fields.append('body')

    if category is not None:
        _validate_category(category)
        discussion.category = category
        update_fields.append('category')

    if len(update_fields) == 1:
        return discussion

    discussion.save(update_fields=update_fields)
    return discussion


def close_discussion(discussion: Discussion, *, closed_by) -> Discussion:
    """Close an open discussion to prevent new replies."""
    _validate_discussion_not_deleted(discussion)

    if discussion.status == DiscussionStatus.CLOSED:
        return discussion

    if discussion.status != DiscussionStatus.OPEN:
        raise InvalidDiscussionStateError(
            f'Discussion "{discussion.slug}" cannot be closed from status '
            f'"{discussion.status}".'
        )

    discussion.status = DiscussionStatus.CLOSED
    discussion.closed_at = timezone.now()
    discussion.closed_by = closed_by
    discussion.save(
        update_fields=['status', 'closed_at', 'closed_by', 'updated_on'],
    )
    return discussion


def reopen_discussion(discussion: Discussion, *, reopened_by=None) -> Discussion:
    """Reopen a closed discussion. Reserved for internal/staff workflows."""
    _validate_discussion_not_deleted(discussion)

    if discussion.status == DiscussionStatus.OPEN:
        return discussion

    if discussion.status != DiscussionStatus.CLOSED:
        raise InvalidDiscussionStateError(
            f'Discussion "{discussion.slug}" cannot be reopened from status '
            f'"{discussion.status}".'
        )

    discussion.status = DiscussionStatus.OPEN
    discussion.closed_at = None
    discussion.closed_by = None
    discussion.save(
        update_fields=['status', 'closed_at', 'closed_by', 'updated_on'],
    )
    return discussion


def soft_delete_discussion(discussion: Discussion, *, deleted_by) -> Discussion:
    """Soft-delete a discussion while preserving replies for audit/knowledge."""
    if discussion.is_deleted:
        raise InvalidDiscussionStateError(
            f'Discussion "{discussion.slug}" is already deleted.'
        )

    discussion.is_deleted = True
    discussion.deleted_at = timezone.now()
    discussion.deleted_by = deleted_by
    discussion.save(
        update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_on'],
    )
    return discussion


def restore_discussion(discussion: Discussion) -> Discussion:
    """Restore a soft-deleted discussion."""
    if not discussion.is_deleted:
        raise InvalidDiscussionStateError(
            f'Discussion "{discussion.slug}" is not deleted.'
        )

    discussion.is_deleted = False
    discussion.deleted_at = None
    discussion.deleted_by = None
    discussion.save(
        update_fields=['is_deleted', 'deleted_at', 'deleted_by', 'updated_on'],
    )
    return discussion
