from django.contrib import admin
from .models import RelatedLink, UsefulLinkCategory


@admin.register(UsefulLinkCategory)
class UsefulLinkCategoryAdmin(admin.ModelAdmin):
    list_display = ('name_fa', 'name_en', 'slug', 'icon', 'display_order', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name_fa', 'name_en', 'slug')
    list_editable = ('display_order', 'is_active')
    prepopulated_fields = {'slug': ('name_en',)}
    ordering = ('display_order', 'name_en')

    fieldsets = (
        ('اطلاعات دسته\u200cبندی', {
            'fields': ('name_fa', 'name_en', 'slug', 'icon', 'description'),
        }),
        ('تنظیمات نمایش', {
            'fields': ('display_order', 'is_active'),
        }),
        ('اطلاعات سیستم', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('created_at', 'updated_at')


@admin.register(RelatedLink)
class RelatedLinkAdmin(admin.ModelAdmin):
    """Admin interface for Related Links."""

    list_display = ('title', 'category', 'link_type', 'is_active', 'order', 'created_on')
    list_filter = ('category', 'link_type', 'is_active', 'created_on')
    search_fields = ('title', 'source_name', 'description', 'url')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', '-created_on')
    autocomplete_fields = ('category',)

    fieldsets = (
        ('اطلاعات لینک', {
            'fields': ('title', 'slug', 'category', 'link_type', 'description', 'source_name', 'url')
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
