from django.conf import settings
from django.db import models

from .constants import NotificationType


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='triggered_notifications',
    )
    notification_type = models.CharField(
        max_length=50,
        choices=NotificationType.choices,
    )
    title = models.CharField(max_length=255)
    message = models.TextField()
    url = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at']),
            models.Index(fields=['recipient', '-created_at']),
            models.Index(fields=['notification_type', '-created_at']),
        ]

    def __str__(self):
        return f'{self.notification_type} → {self.recipient_id}'


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notification_preferences',
    )
    askme_emails = models.BooleanField(
        default=True,
        help_text='Receive AskMe answer emails.',
    )
    ad_emails = models.BooleanField(
        default=True,
        help_text='Receive ad-related emails.',
    )
    comment_notifications = models.BooleanField(
        default=True,
        help_text='Reserved for Phase 2 comment notifications.',
    )
    favorite_notifications = models.BooleanField(
        default=True,
        help_text='Receive in-app notifications when an ad is favorited.',
    )
    weekly_digest = models.BooleanField(
        default=True,
        help_text='Receive the weekly digest email.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Notification preference'
        verbose_name_plural = 'Notification preferences'

    def __str__(self):
        return f'Preferences for {self.user}'

    def allows_email(self, notification_type: str) -> bool:
        if notification_type == NotificationType.ASKME_SPECIALIST_ANSWER:
            return self.askme_emails
        if notification_type in {
            NotificationType.AD_APPROVED,
            NotificationType.AD_REJECTED,
            NotificationType.AD_PRO,
            NotificationType.AD_EXPIRING,
        }:
            return self.ad_emails
        if notification_type == NotificationType.WEEKLY_DIGEST:
            return self.weekly_digest
        return False

    def allows_in_app(self, notification_type: str) -> bool:
        if notification_type == NotificationType.WEEKLY_DIGEST:
            return False
        if notification_type == NotificationType.AD_FAVORITED:
            return self.favorite_notifications
        return True
