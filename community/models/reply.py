from django.conf import settings
from django.db import models

from community.constants import ModerationReason


class Reply(models.Model):
    """Flat reply to a community discussion."""

    discussion = models.ForeignKey(
        'community.Discussion',
        on_delete=models.CASCADE,
        related_name='replies',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='community_replies',
    )
    body = models.TextField()
    approved = models.BooleanField(default=False)
    moderation_reason = models.CharField(
        max_length=50,
        choices=ModerationReason.choices,
        blank=True,
        null=True,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_community_replies',
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Reply'
        verbose_name_plural = 'Replies'
        ordering = ['created_on']
        indexes = [
            models.Index(fields=['discussion', 'approved', 'created_on']),
            models.Index(fields=['approved', '-created_on']),
            models.Index(fields=['author', 'approved']),
            models.Index(fields=['moderation_reason', 'approved']),
        ]

    def __str__(self):
        author_label = self.author.username if self.author else 'deleted user'
        return f'Reply by {author_label} on {self.discussion_id}'
