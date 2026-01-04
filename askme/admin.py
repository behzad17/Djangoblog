"""
Admin interface for Ask Me models with privacy protection.
Admin can see metadata but NOT question/answer content.
"""

from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Moderator, Question


@admin.register(Moderator)
class ModeratorAdmin(admin.ModelAdmin):
    """Admin interface for Moderator model."""
    
    list_display = (
        'user',
        'expert_title',
        'field_specialty',
        'slug',
        'is_active',
        'question_count',
        'answered_count',
        'pending_count',
        'created_on'
    )
    list_filter = ('is_active', 'expert_title', 'field_specialty', 'created_on')
    search_fields = ('user__username', 'user__email', 'expert_title', 'complete_name', 'bio', 'field_specialty', 'slug')
    readonly_fields = ('created_on', 'updated_on')
    
    fieldsets = (
        ('Moderator Information', {
            'fields': ('user', 'expert_title', 'complete_name', 'field_specialty', 'profile_image', 'bio', 'is_active')
        }),
        ('Expert Profile', {
            'fields': ('slug', 'disclaimer'),
            'description': 'Profile page settings. Slug is auto-generated if left blank. Disclaimer is shown on the expert profile page.'
        }),
        ('Contact & Social Links', {
            'fields': ('website_url', 'instagram_url', 'linkedin_url'),
            'description': 'Optional contact and social media links (displayed on expert profile page). URLs must start with https:// or http://'
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )
    
    def question_count(self, obj):
        """Returns the number of questions for this moderator."""
        return obj.questions.count()
    question_count.short_description = 'Total Questions'
    
    def answered_count(self, obj):
        """Returns the number of answered questions."""
        return obj.questions.filter(answered=True).count()
    answered_count.short_description = 'Answered'
    
    def pending_count(self, obj):
        """Returns the number of pending questions."""
        return obj.questions.filter(answered=False).count()
    pending_count.short_description = 'Pending'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    """
    Admin interface for Question model with PRIVACY PROTECTION.
    
    Admin can see metadata (user, moderator, status, timestamps, statistics)
    but NOT the actual question/answer content.
    """
    
    # CRITICAL: Exclude sensitive content fields from admin
    exclude = ('question_text', 'answer_text')
    
    # Show metadata only in list view
    list_display = (
        'id',
        'user_info',
        'moderator_info',
        'status_display',
        'created_on',
        'answered_on',
        'content_stats'
    )
    
    list_filter = ('answered', 'moderator', 'created_on')
    search_fields = ('user__username', 'user__email', 'moderator__user__username', 'moderator__expert_title')
    readonly_fields = ('created_on', 'updated_on', 'answered_on', 'content_metadata', 'privacy_notice')
    
    fieldsets = (
        ('Question Information', {
            'fields': ('user', 'moderator', 'answered', 'created_on', 'updated_on', 'answered_on')
        }),
        ('Content Metadata', {
            'fields': ('content_metadata',),
            'description': 'Statistical information about the question and answer content. Actual content is private and not accessible to admin.'
        }),
        ('Privacy Notice', {
            'fields': ('privacy_notice',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_as_answered', 'mark_as_pending']
    
    def user_info(self, obj):
        """Display user information."""
        return f"{obj.user.username} ({obj.user.email})"
    user_info.short_description = 'User'
    
    def moderator_info(self, obj):
        """Display moderator information."""
        return f"{obj.moderator.user.username} - {obj.moderator.expert_title}"
    moderator_info.short_description = 'Moderator'
    
    def status_display(self, obj):
        """Display answered status with badge."""
        if obj.answered:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Answered</span>'
            )
        return format_html(
            '<span style="color: orange; font-weight: bold;">⏳ Pending</span>'
        )
    status_display.short_description = 'Status'
    
    def content_stats(self, obj):
        """Display content statistics without showing content."""
        if obj is None:
            return '-'
        return format_html(
            'Q: {} chars | A: {} chars',
            len(obj.question_text) if obj.question_text else 0,
            len(obj.answer_text) if obj.answer_text else 0
        )
    content_stats.short_description = 'Content Stats'
    
    def content_metadata(self, obj):
        """Display detailed content metadata without showing content."""
        if obj is None:
            return format_html(
                '<div style="padding: 10px; background: #f9f9f9; border-left: 3px solid #007bff; border-radius: 3px;">'
                '<em style="color: #666; font-size: 0.9em;">Content statistics will be available after the question is created.</em>'
                '</div>'
            )
        return format_html(
            '<div style="padding: 10px; background: #f9f9f9; border-left: 3px solid #007bff; border-radius: 3px;">'
            '<strong>Question:</strong> {} characters, {} words<br>'
            '<strong>Answer:</strong> {} characters, {} words<br>'
            '<em style="color: #666; font-size: 0.9em;">Content is private and accessible only to the user and assigned moderator.</em>'
            '</div>',
            len(obj.question_text) if obj.question_text else 0,
            len(obj.question_text.split()) if obj.question_text else 0,
            len(obj.answer_text) if obj.answer_text else 0,
            len(obj.answer_text.split()) if obj.answer_text else 0,
        )
    content_metadata.short_description = 'Content Statistics'
    
    def privacy_notice(self, obj):
        """Display privacy notice."""
        return format_html(
            '<div style="padding: 15px; background: #fff3cd; border: 1px solid #ffc107; border-radius: 5px;">'
            '<strong>⚠️ Privacy Protection:</strong><br>'
            'Question and answer content is private and accessible only to:<br>'
            '• The user who asked the question<br>'
            '• The assigned moderator<br><br>'
            'Admin can view metadata (timestamps, status, user info, content statistics) but NOT the actual content.'
            '</div>'
        )
    privacy_notice.short_description = 'Privacy Notice'
    
    # CRITICAL: Ensure content fields never appear even if accidentally included
    def get_fields(self, request, obj=None):
        """Override to ensure content fields are never included."""
        fields = super().get_fields(request, obj)
        # Remove content fields if somehow included
        return [f for f in fields if f not in ('question_text', 'answer_text')]
    
    # CRITICAL: Prevent content search
    def get_search_fields(self, request):
        """Only allow searching in metadata fields, not content."""
        return ('user__username', 'user__email', 'moderator__user__username', 'moderator__expert_title')
    
    def mark_as_answered(self, request, queryset):
        """Bulk action to mark questions as answered (metadata only)."""
        updated = queryset.update(answered=True, answered_on=timezone.now())
        self.message_user(request, f"{updated} question(s) marked as answered.")
    mark_as_answered.short_description = 'Mark selected as answered'
    
    def mark_as_pending(self, request, queryset):
        """Bulk action to mark questions as pending (metadata only)."""
        updated = queryset.update(answered=False, answered_on=None)
        self.message_user(request, f"{updated} question(s) marked as pending.")
    mark_as_pending.short_description = 'Mark selected as pending'
