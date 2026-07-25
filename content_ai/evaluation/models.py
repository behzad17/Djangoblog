"""AI generation feedback model for human editorial evaluation."""

from __future__ import annotations

import uuid

from django.conf import settings
from django.db import models

from content_ai.evaluation.constants import AIFeedbackRating


class AIGenerationFeedback(models.Model):
    """
    Structured editorial feedback for one AI generation preview.

    Collection only — no prompt optimisation or analytics aggregation.
    """

    generation_id = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        db_index=True,
    )
    prompt_task = models.CharField(max_length=64, db_index=True)
    prompt_version = models.CharField(max_length=50, blank=True, db_index=True)
    provider = models.CharField(max_length=100, blank=True, db_index=True)
    model_name = models.CharField(max_length=100, blank=True, db_index=True)
    language = models.CharField(max_length=32, blank=True, db_index=True)
    rating = models.CharField(
        max_length=32,
        choices=AIFeedbackRating.choices,
        db_index=True,
    )
    reasons = models.JSONField(
        default=list,
        blank=True,
        help_text='List of reason codes (extendable).',
    )
    comment = models.TextField(blank=True)
    accepted = models.BooleanField(default=False)
    regenerated = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='content_ai_generation_feedback',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'AI generation feedback'
        verbose_name_plural = 'AI generation feedback'
        indexes = [
            models.Index(fields=['rating', '-created_at']),
            models.Index(fields=['prompt_version', '-created_at']),
            models.Index(fields=['provider', 'model_name', '-created_at']),
        ]

    def __str__(self):
        return (
            f'Feedback {self.generation_id} '
            f'({self.rating}/accepted={self.accepted})'
        )
