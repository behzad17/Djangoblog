from django.contrib import admin
from django.utils.html import format_html
from .models import Post, Comment, Category, UserProfile, PageView, PostViewCount
from django_summernote.admin import SummernoteModelAdmin

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Admin interface for Category model."""
    list_display = ('name', 'slug', 'post_count', 'created_on')
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['name']
    
    def post_count(self, obj):
        """Returns the number of published posts in this category."""
        return obj.posts.filter(status=1, is_deleted=False).count()
    post_count.short_description = 'Published Posts'

@admin.register(Post)
class PostAdmin(SummernoteModelAdmin):

    list_display = ('title', 'slug', 'category', 'status', 'pinned', 'pinned_row', 'url_status', 'is_deleted', 'deleted_status', 'created_on')
    search_fields = ['title', 'content', 'external_url']
    list_filter = ('status', 'category', 'pinned', 'url_approved', 'is_deleted', 'created_on',)
    prepopulated_fields = {'slug': ('title',)}
    summernote_fields = ('content',)
    fieldsets = (
        ('Post Information', {
            'fields': ('title', 'slug', 'author', 'category', 'status', 'pinned', 'pinned_row')
        }),
        ('Content', {
            'fields': ('excerpt', 'content', 'featured_image')
        }),
        ('External URL', {
            'fields': ('external_url', 'url_approved'),
            'description': 'Users can add an external URL. Admin must approve it before it will be displayed.'
        }),
        ('Soft Delete', {
            'fields': ('is_deleted', 'deleted_at', 'deleted_by'),
            'description': 'Soft delete information. Deleted posts are hidden from public views.',
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_on', 'updated_on', 'deleted_at', 'deleted_by')
    
    def url_status(self, obj):
        """Display URL approval status."""
        if not obj.external_url:
            return "No URL"
        elif obj.url_approved:
            return "✓ Approved"
        else:
            return "⏳ Pending"
    url_status.short_description = 'URL Status'
    
    def deleted_status(self, obj):
        """Display soft delete status."""
        if obj.is_deleted:
            deleted_info = f"Deleted"
            if obj.deleted_at:
                deleted_info += f" ({obj.deleted_at.strftime('%Y-%m-%d')})"
            if obj.deleted_by:
                deleted_info += f" by {obj.deleted_by.username}"
            return format_html(
                '<span style="color: red; font-weight: bold;">🗑️ {}</span>',
                deleted_info
            )
        return format_html('<span style="color: green;">✓ Active</span>')
    deleted_status.short_description = 'Delete Status'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    list_display = ('user', 'expert_status', 'expert_since', 'site_verified_status', 'post_count')
    list_filter = ('can_publish_without_approval', 'is_site_verified', 'expert_since', 'site_verified_at')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('expert_since', 'site_verified_at')
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Site Verification', {
            'fields': ('is_site_verified', 'site_verified_at'),
            'description': 'Site verification is required for write actions (posts, comments, ads).'
        }),
        ('Expert Access', {
            'fields': ('can_publish_without_approval', 'expert_since'),
            'description': 'Grant or revoke expert publishing access. Expert users can publish posts without admin approval.'
        }),
    )
    
    def site_verified_status(self, obj):
        """Display site verification status."""
        if obj.is_site_verified:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Verified</span>'
            )
        return format_html(
            '<span style="color: red;">✗ Not Verified</span>'
        )
    site_verified_status.short_description = 'Site Verified'
    
    def expert_status(self, obj):
        """Display expert status with colored badge."""
        if obj.can_publish_without_approval:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Expert</span>'
            )
        return format_html(
            '<span style="color: gray;">Regular User</span>'
        )
    expert_status.short_description = 'Status'
    
    def post_count(self, obj):
        """Display count of published posts by this user."""
        return obj.user.blog_posts.filter(status=1, is_deleted=False).count()
    post_count.short_description = 'Published Posts'
    
    def save_model(self, request, obj, form, change):
        """Set expert_since when access is granted for the first time."""
        if obj.can_publish_without_approval and not obj.expert_since:
            from django.utils import timezone
            obj.expert_since = timezone.now()
        elif not obj.can_publish_without_approval:
            obj.expert_since = None
        super().save_model(request, obj, form, change)

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin interface for comment moderation."""
    
    list_display = (
        'id',
        'body_preview',
        'author',
        'post',
        'approved',  # Must be in list_display to use in list_editable
        'approval_status',
        'moderation_reason_display',
        'created_on',
        'reviewed_info'
    )
    
    list_filter = (
        'approved',
        'moderation_reason',
        'created_on',
        'reviewed_at',
    )
    
    search_fields = ('body', 'author__username', 'post__title')
    
    list_editable = ('approved',)  # Quick approve/reject
    
    readonly_fields = ('created_on', 'reviewed_by', 'reviewed_at')
    
    actions = ['approve_comments', 'reject_comments']
    
    fieldsets = (
        ('Comment Content', {
            'fields': ('body', 'post', 'author')
        }),
        ('Moderation', {
            'fields': (
                'approved',
                'moderation_reason',
                'reviewed_by',
                'reviewed_at'
            )
        }),
        ('Timestamps', {
            'fields': ('created_on',),
            'classes': ('collapse',)
        }),
    )
    
    def body_preview(self, obj):
        """Show first 50 characters of comment."""
        if len(obj.body) > 50:
            return obj.body[:50] + '...'
        return obj.body
    body_preview.short_description = 'Comment'
    
    def approval_status(self, obj):
        """Color-coded approval status."""
        if obj.approved:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Approved</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">⏳ Pending</span>'
        )
    approval_status.short_description = 'Status'
    
    def moderation_reason_display(self, obj):
        """Display moderation reason with icon."""
        if not obj.moderation_reason:
            return '-'
        reasons = {
            'new_user': '👤 New User',
            'contains_link': '🔗 Contains Link',
            'manual_review': '📋 Manual Review',
        }
        return reasons.get(obj.moderation_reason, obj.moderation_reason)
    moderation_reason_display.short_description = 'Reason'
    
    def reviewed_info(self, obj):
        """Show who reviewed and when."""
        if obj.reviewed_by and obj.reviewed_at:
            return f"{obj.reviewed_by.username} ({obj.reviewed_at.strftime('%Y-%m-%d %H:%M')})"
        return '-'
    reviewed_info.short_description = 'Reviewed By'
    
    def approve_comments(self, request, queryset):
        """Bulk approve action."""
        from django.utils import timezone
        updated = queryset.update(
            approved=True,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} comment(s) approved.")
    approve_comments.short_description = 'Approve selected comments'
    
    def reject_comments(self, request, queryset):
        """Bulk reject action."""
        from django.utils import timezone
        updated = queryset.update(
            approved=False,
            reviewed_by=request.user,
            reviewed_at=timezone.now()
        )
        self.message_user(request, f"{updated} comment(s) rejected.")
    reject_comments.short_description = 'Reject selected comments'
    
    def save_model(self, request, obj, form, change):
        """Track who reviewed the comment."""
        from django.utils import timezone
        if change and 'approved' in form.changed_data:
            obj.reviewed_by = request.user
            obj.reviewed_at = timezone.now()
        super().save_model(request, obj, form, change)


@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    """Admin interface for PageView model."""
    list_display = ('post', 'user', 'viewed_at', 'ip_hash_short', 'is_bot', 'referer_short')
    list_filter = ('is_bot', 'viewed_at', 'post')
    search_fields = ['post__title', 'url_path', 'user__username']
    readonly_fields = ('viewed_at', 'ip_hash', 'user_agent_hash')
    date_hierarchy = 'viewed_at'
    ordering = ['-viewed_at']
    
    fieldsets = (
        ('View Information', {
            'fields': ('post', 'url_path', 'user', 'viewed_at')
        }),
        ('Tracking Data', {
            'fields': ('session_key', 'ip_hash', 'user_agent_hash', 'is_bot'),
            'description': 'Anonymized tracking data for privacy compliance.'
        }),
        ('Referer', {
            'fields': ('referer',),
            'classes': ('collapse',)
        }),
    )
    
    def ip_hash_short(self, obj):
        """Display shortened IP hash."""
        return obj.ip_hash[:8] + '...' if obj.ip_hash else 'N/A'
    ip_hash_short.short_description = 'IP Hash'
    
    def referer_short(self, obj):
        """Display shortened referer."""
        if obj.referer:
            return obj.referer[:50] + '...' if len(obj.referer) > 50 else obj.referer
        return '-'
    referer_short.short_description = 'Referer'


@admin.register(PostViewCount)
class PostViewCountAdmin(admin.ModelAdmin):
    """Admin interface for PostViewCount model."""
    list_display = ('post', 'total_views', 'unique_views', 'last_updated')
    search_fields = ['post__title']
    readonly_fields = ('last_updated',)
    ordering = ['-total_views']
    
    fieldsets = (
        ('Post', {
            'fields': ('post',)
        }),
        ('View Statistics', {
            'fields': ('total_views', 'unique_views', 'last_updated'),
            'description': 'Aggregated view counts. Updated automatically when views are tracked.'
        }),
    )
