from django.contrib import admin

from community.models import CommunityCategory, Discussion, Reply


@admin.register(CommunityCategory)
class CommunityCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'display_order', 'is_active', 'created_on')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug')
    ordering = ('display_order', 'name')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Discussion)
class DiscussionAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'author',
        'category',
        'status',
        'reply_count',
        'is_deleted',
        'last_activity_at',
        'created_on',
    )
    list_filter = ('status', 'is_deleted', 'category')
    search_fields = ('title', 'slug', 'body')
    readonly_fields = (
        'reply_count',
        'last_activity_at',
        'created_on',
        'updated_on',
        'deleted_at',
        'closed_at',
    )
    raw_id_fields = ('author', 'deleted_by', 'closed_by')
    date_hierarchy = 'created_on'


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = (
        'discussion',
        'author',
        'approved',
        'moderation_reason',
        'created_on',
    )
    list_filter = ('approved', 'moderation_reason')
    search_fields = ('body', 'discussion__title')
    readonly_fields = ('created_on', 'updated_on', 'reviewed_at')
    raw_id_fields = ('discussion', 'author', 'reviewed_by')
    date_hierarchy = 'created_on'
