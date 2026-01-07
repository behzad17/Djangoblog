from django.contrib import admin
from django.utils.html import format_html
from .models import AdCategory, Ad, AdComment


@admin.register(AdCategory)
class AdCategoryAdmin(admin.ModelAdmin):
    """Admin interface for advertisement categories."""

    list_display = ("name", "slug", "ad_count", "created_on")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    """Admin interface for advertisements with moderation controls."""

    list_display = (
        "title",
        "category",
        "owner",
        "is_active",
        "is_approved",
        "is_featured",
        "featured_priority",
        "url_status",
        "social_urls_status",
        "start_date",
        "end_date",
        "created_on",
    )
    list_filter = (
        "category",
        "owner",
        "is_active",
        "is_approved",
        "is_featured",
        "url_approved",
        "social_urls_approved",
        "start_date",
        "end_date",
    )
    list_editable = ("is_featured", "featured_priority")
    search_fields = ("title", "target_url", "category__name", "city", "address", "phone")
    prepopulated_fields = {"slug": ("title",)}
    readonly_fields = ("created_on", "updated_on")

    fieldsets = (
        (
            "Ad Information",
            {
                "fields": (
                    "title",
                    "slug",
                    "category",
                    "owner",
                )
            },
        ),
        (
            "Media",
            {
                "fields": ("image",),
                "description": "Upload an image. It will be displayed at 250×500 in the front-end.",
            },
        ),
        (
            "Target URL",
            {
                "fields": ("target_url", "url_approved"),
                "description": "Advertiser-provided URL. Must be approved before being used on the site.",
            },
        ),
        (
            "Location & Contact Information",
            {
                "fields": ("city", "address", "phone"),
                "description": "Location and contact information displayed publicly on the ad detail page.",
            },
        ),
        (
            "Social Media URLs",
            {
                "fields": ("instagram_url", "telegram_url", "website_url", "social_urls_approved"),
                "description": "Social media and website URLs. Must be approved before links become clickable on the site.",
            },
        ),
        (
            "Visibility & Scheduling",
            {
                "fields": ("is_active", "is_approved", "start_date", "end_date"),
                "description": "Control when this ad is visible to users.",
            },
        ),
        (
            "Featured Ad",
            {
                "fields": ("is_featured", "featured_priority", "featured_until"),
                "description": "Featured ads appear first in listings (positions 1-39 on page 1). Set featured_priority (1-39) to control exact position. Lower numbers = higher priority. Leave priority blank for automatic ordering by date.",
            },
        ),
        (
            "Timestamps",
            {
                "fields": ("created_on", "updated_on"),
                "classes": ("collapse",),
            },
        ),
    )

    def url_status(self, obj):
        """Display URL approval status with a small label."""
        if not obj.target_url:
            return "No URL"
        if obj.url_approved:
            return format_html('<span style="color: green;">✓ URL Approved</span>')
        return format_html('<span style="color: orange;">⏳ URL Pending</span>')

    url_status.short_description = "URL Status"
    
    def social_urls_status(self, obj):
        """Display social URLs approval status."""
        has_social = bool(obj.instagram_url or obj.telegram_url or obj.website_url)
        if not has_social:
            return "No Social URLs"
        if obj.social_urls_approved:
            return format_html('<span style="color: green;">✓ Social URLs Approved</span>')
        return format_html('<span style="color: orange;">⏳ Social URLs Pending</span>')
    
    social_urls_status.short_description = "Social URLs Status"


@admin.register(AdComment)
class AdCommentAdmin(admin.ModelAdmin):
    """Admin interface for ad comments."""
    
    list_display = (
        'id',
        'body_preview',
        'author',
        'ad',
        'is_deleted',
        'created_on',
    )
    
    list_filter = (
        'is_deleted',
        'created_on',
    )
    
    search_fields = ('body', 'author__username', 'ad__title')
    
    readonly_fields = ('created_on', 'updated_on')
    
    fieldsets = (
        ('Comment Content', {
            'fields': ('body', 'ad', 'author')
        }),
        ('Status', {
            'fields': ('is_deleted',)
        }),
        ('Timestamps', {
            'fields': ('created_on', 'updated_on'),
            'classes': ('collapse',)
        }),
    )
    
    def body_preview(self, obj):
        """Show first 50 characters of comment."""
        if len(obj.body) > 50:
            return obj.body[:50] + '...'
        return obj.body
    body_preview.short_description = 'Comment'


# Register your models here.
