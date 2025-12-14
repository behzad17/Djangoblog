from django.contrib import admin
from django.utils.html import format_html
from .models import Post, Comment, Category, UserProfile
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
        return obj.posts.filter(status=1).count()
    post_count.short_description = 'Published Posts'

@admin.register(Post)
class PostAdmin(SummernoteModelAdmin):

    list_display = ('title', 'slug', 'category', 'status', 'pinned', 'pinned_row', 'url_status', 'created_on')
    search_fields = ['title', 'content', 'external_url']
    list_filter = ('status', 'category', 'pinned', 'url_approved', 'created_on',)
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
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ('created_on', 'updated_on')
    
    def url_status(self, obj):
        """Display URL approval status."""
        if not obj.external_url:
            return "No URL"
        elif obj.url_approved:
            return "✓ Approved"
        else:
            return "⏳ Pending"
    url_status.short_description = 'URL Status'

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin interface for UserProfile model."""
    list_display = ('user', 'expert_status', 'expert_since', 'post_count')
    list_filter = ('can_publish_without_approval', 'expert_since')
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('expert_since',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Expert Access', {
            'fields': ('can_publish_without_approval', 'expert_since'),
            'description': 'Grant or revoke expert publishing access. Expert users can publish posts without admin approval.'
        }),
    )
    
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
        return obj.user.blog_posts.filter(status=1).count()
    post_count.short_description = 'Published Posts'
    
    def save_model(self, request, obj, form, change):
        """Set expert_since when access is granted for the first time."""
        if obj.can_publish_without_approval and not obj.expert_since:
            from django.utils import timezone
            obj.expert_since = timezone.now()
        elif not obj.can_publish_without_approval:
            obj.expert_since = None
        super().save_model(request, obj, form, change)

# Register your models here.
admin.site.register(Comment)
