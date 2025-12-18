"""
Models for the 'Ask Me' Q&A system with moderators.
"""

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField


class Moderator(models.Model):
    """
    Represents a moderator/expert consultant.
    Admin assigns users as moderators with expert titles.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='moderator_profile',
        help_text="The user account associated with this moderator"
    )
    expert_title = models.CharField(
        max_length=100,
        help_text="Expert title (e.g., 'Lawyer', 'Doctor', 'Accountant')"
    )
    complete_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Complete/full name to display in Ask Me boxes (if empty, will use user's full name or username)"
    )
    profile_image = CloudinaryField(
        'image',
        default='placeholder',
        help_text="Moderator profile image"
    )
    bio = models.TextField(
        blank=True,
        help_text="Short bio about the moderator"
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this moderator is currently active"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['expert_title', 'user__username']
        verbose_name_plural = "Moderators"

    def __str__(self):
        return f"{self.get_display_name()} - {self.expert_title}"
    
    def get_display_name(self):
        """Returns the complete name, or falls back to user's full name or username."""
        try:
            # Safely get complete_name, handling case where field might not exist in DB yet
            complete_name = getattr(self, 'complete_name', None)
            if complete_name:
                return complete_name
        except (AttributeError, Exception):
            pass
        # Fallback to user's full name or username
        return self.user.get_full_name() or self.user.username
    
    def question_count(self):
        """Returns the number of questions for this moderator."""
        return self.questions.count()
    
    def answered_count(self):
        """Returns the number of answered questions."""
        return self.questions.filter(answered=True).count()
    
    def pending_count(self):
        """Returns the number of pending questions."""
        return self.questions.filter(answered=False).count()


class Question(models.Model):
    """
    Represents a private Q&A thread between a user and a moderator.
    
    PRIVACY NOTE: Question and answer content is private and only visible
    to the user who asked it and the assigned moderator. Admin can see
    metadata (timestamps, status, user info) but NOT the actual content.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='asked_questions',
        help_text="The user who asked the question"
    )
    moderator = models.ForeignKey(
        Moderator,
        on_delete=models.CASCADE,
        related_name='questions',
        help_text="The moderator assigned to answer this question"
    )
    
    # PRIVATE FIELDS - Not visible in admin (excluded in admin.py)
    question_text = models.TextField(
        help_text="The question asked by the user (PRIVATE - visible only to user and moderator)"
    )
    answer_text = models.TextField(
        blank=True,
        help_text="The answer provided by the moderator (PRIVATE - visible only to user and moderator)"
    )
    
    # PUBLIC METADATA - Visible in admin
    answered = models.BooleanField(
        default=False,
        help_text="Whether the question has been answered"
    )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    answered_on = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the question was answered"
    )

    class Meta:
        ordering = ['-created_on']
        verbose_name_plural = "Questions"

    def __str__(self):
        """String representation without content (for privacy)."""
        return f"Question #{self.id} - {self.user.username} → {self.moderator.expert_title}"
    
    def get_question_length(self):
        """Get question length in characters (for metadata display)."""
        return len(self.question_text)
    
    def get_answer_length(self):
        """Get answer length in characters (for metadata display)."""
        return len(self.answer_text) if self.answer_text else 0
    
    def get_question_word_count(self):
        """Get question word count (for metadata display)."""
        return len(self.question_text.split())
    
    def get_answer_word_count(self):
        """Get answer word count (for metadata display)."""
        return len(self.answer_text.split()) if self.answer_text else 0
