from django import forms
from django.contrib import admin
from django.utils.html import format_html

from .models import RelatedLink, UsefulLinkCategory


class RelatedLinkAdminForm(forms.ModelForm):
    class Meta:
        model = RelatedLink
        fields = '__all__'
        widgets = {
            'short_description': forms.Textarea(
                attrs={
                    'rows': 2,
                    'maxlength': 160,
                    'style': 'max-width: 42rem;',
                    'placeholder': 'مثال: وب‌سایت رسمی مالیات، personnummer و خدمات مالیاتی دیجیتال.',
                },
            ),
        }


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
    """Editorial admin for Useful Links resources."""

    form = RelatedLinkAdminForm
    list_display = (
        'thumbnail_list',
        'title',
        'category',
        'link_type',
        'source_name',
        'order',
        'is_active',
    )
    list_display_links = ('title',)
    list_filter = ('category', 'link_type', 'is_active')
    search_fields = ('title', 'source_name', 'short_description')
    list_editable = ('order', 'is_active')
    list_per_page = 50
    ordering = ('order', 'title')
    autocomplete_fields = ('category',)

    fieldsets = (
        ('اطلاعات اصلی', {
            'fields': (
                'title',
                'url',
                'category',
                'link_type',
                'source_name',
            ),
        }),
        ('نمایش در وب\u200cسایت', {
            'fields': (
                'cover_image',
                'thumbnail_preview',
                'short_description',
            ),
            'description': (
                'توضیح کوتاه در فهرست لینک\u200cهای مفید نمایش داده می\u200cشود '
                'و باید به\u200cاختصار توضیح دهد این منبع چرا مفید است.'
            ),
        }),
        ('انتشار', {
            'fields': (
                'order',
                'is_active',
            ),
        }),
        ('متاداده آینده', {
            'fields': (),
            'description': (
                'فیلدهای برنامه\u200cریزی\u200cشده برای فازهای بعدی: '
                'منبع رسمی، پیشنهاد پیوند، زبان، ویژه.'
            ),
            'classes': ('collapse',),
        }),
        ('سیستم', {
            'fields': (
                'slug',
                'description',
                'created_on',
                'updated_on',
            ),
            'classes': ('collapse',),
        }),
    )

    readonly_fields = ('thumbnail_preview', 'created_on', 'updated_on')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        field = super().formfield_for_dbfield(db_field, request, **kwargs)
        if db_field.name == 'cover_image':
            field.label = 'تصویر بندانگشتی'
        elif db_field.name == 'short_description':
            field.help_text = (
                'این توضیح کوتاه در فهرست لینک\u200cهای مفید نمایش داده می\u200cشود '
                'و باید به\u200cاختصار توضیح دهد این منبع چرا مفید است.'
            )
        return field

    @admin.display(description='بندانگشتی')
    def thumbnail_list(self, obj):
        if obj and obj.cover_image:
            return format_html(
                '<img src="{}" width="48" height="48" '
                'style="object-fit: cover; border-radius: 6px; '
                'border: 1px solid #e5e7eb; background: #f9fafb;" alt="">',
                obj.cover_image.url,
            )
        return format_html(
            '<span style="display: inline-flex; align-items: center; '
            'justify-content: center; width: 48px; height: 48px; '
            'border-radius: 6px; background: #f3f4f6; color: #9ca3af; '
            'font-size: 11px; border: 1px dashed #d1d5db;">—</span>',
        )

    @admin.display(description='پیش\u200cنمایش تصویر')
    def thumbnail_preview(self, obj):
        if obj and obj.cover_image:
            return format_html(
                '<img src="{}" style="max-height: 120px; max-width: 240px; '
                'object-fit: cover; border-radius: 8px; '
                'border: 1px solid #e5e7eb;" alt="">',
                obj.cover_image.url,
            )
        return format_html(
            '<div style="display: flex; align-items: center; justify-content: center; '
            'width: 240px; height: 120px; border-radius: 8px; background: #f9fafb; '
            'color: #9ca3af; font-size: 13px; border: 1px dashed #d1d5db;">'
            'بدون تصویر'
            '</div>',
        )
