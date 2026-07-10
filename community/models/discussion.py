from django.conf import settings
from django.db import models
from django.db.models import Q

from community.constants import DiscussionStatus


class Discussion(models.Model):
    """Top-level community thread."""

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='community_discussions',
    )
    category = models.ForeignKey(
        'community.CommunityCategory',
        on_delete=models.PROTECT,
        related_name='discussions',
    )
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, allow_unicode=True)
    body = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=DiscussionStatus.choices,
        default=DiscussionStatus.OPEN,
    )
    reply_count = models.PositiveIntegerField(default=0)
    last_activity_at = models.DateTimeField()
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deleted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='soft_deleted_community_discussions',
    )
    closed_at = models.DateTimeField(null=True, blank=True)
    closed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='closed_community_discussions',
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Discussion'
        verbose_name_plural = 'Discussions'
        ordering = ['-last_activity_at']
        indexes = [
            models.Index(fields=['is_deleted', 'status', '-last_activity_at']),
            models.Index(
                fields=['category', 'is_deleted', '-last_activity_at'],
            ),
            models.Index(fields=['author', '-created_on']),
            models.Index(fields=['is_deleted', '-created_on']),
        ]
        constraints = [
            models.CheckConstraint(
                check=Q(reply_count__gte=0),
                name='community_discussion_reply_count_gte_0',
            ),
        ]

    def __str__(self):
        return self.title
