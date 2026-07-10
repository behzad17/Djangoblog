from community.constants import DiscussionStatus


def can_reply(user, discussion) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    if discussion.is_deleted:
        return False
    if discussion.status != DiscussionStatus.OPEN:
        return False
    profile = getattr(user, 'profile', None)
    if profile is None or not profile.is_site_verified:
        return False
    return True


def can_close(user, discussion) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    if discussion.is_deleted:
        return False
    if discussion.status != DiscussionStatus.OPEN:
        return False
    if getattr(user, 'is_staff', False):
        return True
    return discussion.author_id == user.pk


def can_create_discussion(user) -> bool:
    if not getattr(user, 'is_authenticated', False):
        return False
    profile = getattr(user, 'profile', None)
    return profile is not None and profile.is_site_verified
