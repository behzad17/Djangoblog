from django.contrib import admin
from .models import Post, Comment, Category
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

# Register your models here.
admin.site.register(Comment)
