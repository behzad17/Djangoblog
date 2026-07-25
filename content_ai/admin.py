from django.contrib import admin

from content_ai.models import AIJob


@admin.register(AIJob)
class AIJobAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'job_type',
        'status',
        'provider',
        'model_name',
        'prompt_version',
        'created_by',
        'started_at',
        'completed_at',
        'created_at',
        'updated_at',
    )
    list_filter = (
        'job_type',
        'status',
        'provider',
        'created_at',
    )
    search_fields = (
        'provider',
        'model_name',
        'prompt_version',
        'created_by__username',
        'created_by__email',
    )
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at',
        'updated_at',
        'started_at',
        'completed_at',
    )
    raw_id_fields = ('created_by',)
    date_hierarchy = 'created_at'
