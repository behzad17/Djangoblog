"""Admin for AI generation feedback (read-only after creation)."""

from django.contrib import admin

from content_ai.evaluation.models import AIGenerationFeedback


@admin.register(AIGenerationFeedback)
class AIGenerationFeedbackAdmin(admin.ModelAdmin):
    list_display = (
        'generation_id',
        'prompt_task',
        'prompt_version',
        'provider',
        'model_name',
        'language',
        'rating',
        'accepted',
        'regenerated',
        'created_by',
        'created_at',
    )
    list_filter = (
        'prompt_version',
        'provider',
        'model_name',
        'rating',
        'language',
        'accepted',
        'regenerated',
        'created_at',
    )
    search_fields = (
        'generation_id',
        'prompt_task',
        'prompt_version',
        'provider',
        'model_name',
        'comment',
        'created_by__username',
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    raw_id_fields = ('created_by',)
    readonly_fields = (
        'generation_id',
        'prompt_task',
        'prompt_version',
        'provider',
        'model_name',
        'language',
        'rating',
        'reasons',
        'comment',
        'accepted',
        'regenerated',
        'created_by',
        'created_at',
        'metadata',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        # Allow viewing change form as read-only; block saves via readonly fields.
        return request.user.is_staff

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
