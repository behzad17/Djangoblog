from django.conf import settings
from django.db import models

from content_ai.constants import AIJobStatus, AIJobType


class AIJob(models.Model):
    """
    Tracks a Content AI execution.

    This is not a content model. Generated Blog Posts and Advertisements
    remain owned by the Blog and Ads applications.
    """

    job_type = models.CharField(
        max_length=20,
        choices=AIJobType.choices,
    )
    status = models.CharField(
        max_length=20,
        choices=AIJobStatus.choices,
        default=AIJobStatus.PENDING,
    )
    provider = models.CharField(max_length=100, blank=True)
    model_name = models.CharField(max_length=100, blank=True)
    prompt_version = models.CharField(max_length=50, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='content_ai_jobs',
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI job'
        verbose_name_plural = 'AI jobs'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['job_type', '-created_at']),
        ]

    def __str__(self):
        return f'AIJob {self.pk} ({self.job_type}/{self.status})'
