from django.db import models


class DiscussionStatus(models.TextChoices):
    OPEN = 'open', 'Open'
    CLOSED = 'closed', 'Closed'
    HIDDEN = 'hidden', 'Hidden'


class ModerationReason(models.TextChoices):
    NEW_USER = 'new_user', 'New user (first 5 comments)'
    CONTAINS_LINK = 'contains_link', 'Contains link'
    MANUAL_REVIEW = 'manual_review', 'Manual review'
