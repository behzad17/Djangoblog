from django.contrib.auth import get_user_model
from django.db.models import Q

from community.models import CommunityCategory, Discussion, Reply
from community.selectors.discussions import PUBLIC_DISCUSSION_STATUSES

User = get_user_model()


def _public_discussion_filter(prefix=''):
    """Build filter kwargs for public, non-deleted discussions."""
    field = f'{prefix}__' if prefix else ''
    return {
        f'{field}is_deleted': False,
        f'{field}status__in': PUBLIC_DISCUSSION_STATUSES,
    }


def get_community_home_stats():
    """
    Compact homepage counts using the same visibility rules as public pages.
    """
    discussion_filter = _public_discussion_filter()

    total_discussions = Discussion.objects.filter(**discussion_filter).count()

    total_replies = Reply.objects.filter(
        approved=True,
        **_public_discussion_filter('discussion'),
    ).count()

    total_categories = CommunityCategory.objects.filter(is_active=True).count()

    active_members = User.objects.filter(
        Q(
            community_discussions__is_deleted=False,
            community_discussions__status__in=PUBLIC_DISCUSSION_STATUSES,
        )
        | Q(
            community_replies__approved=True,
            community_replies__discussion__is_deleted=False,
            community_replies__discussion__status__in=PUBLIC_DISCUSSION_STATUSES,
        )
    ).distinct().count()

    return {
        'total_discussions': total_discussions,
        'total_replies': total_replies,
        'active_members': active_members,
        'categories': total_categories,
    }
