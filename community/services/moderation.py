from django.conf import settings
from django.contrib.auth import get_user_model

from blog.utils import contains_link
from community.constants import ModerationReason
from community.models import Reply

User = get_user_model()


def _approved_reply_count(user) -> int:
    if user is None or not getattr(user, 'is_authenticated', False):
        return 0
    return Reply.objects.filter(author=user, approved=True).count()


def should_auto_approve_reply(user, body: str) -> tuple[bool, str | None]:
    """
    Decide whether a reply should be auto-approved.

    Returns:
        (approved, moderation_reason) where moderation_reason is None when approved.
    """
    if contains_link(body):
        return False, ModerationReason.CONTAINS_LINK

    trust_threshold = settings.COMMUNITY_TRUST_REPLY_COUNT
    if _approved_reply_count(user) < trust_threshold:
        return False, ModerationReason.NEW_USER

    return True, None
