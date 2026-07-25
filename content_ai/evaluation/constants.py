"""Editorial AI evaluation constants (extendable, no auto-optimisation)."""

from django.db import models


class AIFeedbackRating(models.TextChoices):
    EXCELLENT = 'excellent', 'Excellent'
    GOOD = 'good', 'Good'
    NEEDS_IMPROVEMENT = 'needs_improvement', 'Needs Improvement'
    REJECTED = 'rejected', 'Rejected'


class AIFeedbackReason(models.TextChoices):
    """Extendable reason codes stored as a list on feedback rows."""

    TOO_LONG = 'too_long', 'Too long'
    TOO_SHORT = 'too_short', 'Too short'
    WRONG_TONE = 'wrong_tone', 'Wrong tone'
    HALLUCINATION = 'hallucination', 'Hallucination'
    GRAMMAR = 'grammar', 'Grammar'
    FORMATTING = 'formatting', 'Formatting'
    OFF_TOPIC = 'off_topic', 'Off-topic'
    POOR_STRUCTURE = 'poor_structure', 'Poor structure'
    OTHER = 'other', 'Other'


VALID_FEEDBACK_REASON_VALUES = frozenset(
    choice.value for choice in AIFeedbackReason
)
