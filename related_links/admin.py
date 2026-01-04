from django.contrib import admin
from .models import RelatedLink


@admin.register(RelatedLink)
class RelatedLinkAdmin(admin.ModelAdmin):
    """Admin interface for Related Links."""
    
    list_display = ('title', 'link_type', 'is_active', 'order', 'created_on')
    list_filter = ('link_type', 'is_active', 'created_on')
    search_fields = ('title', 'source_name', 'description', 'url')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', '-created_on')
    
    fieldsets = (
        ('اطلاعات لینک', {
            'fields': ('title', 'slug', 'link_type', 'description', 'source_name', 'url')
        }),
        ('رسانه', {
            'fields': ('cover_image',),
            'description': 'تصویر کاور اختیاری برای نمایش در کارت لینک'
        }),
        ('تنظیمات نمایش', {
            'fields': ('is_active', 'order')
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_on', 'updated_on')

