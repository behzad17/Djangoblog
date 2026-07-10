from django.contrib import admin
from django.utils.html import format_html

from .models import Notification, NotificationPreference


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
  list_display = (
    'id',
    'recipient',
    'notification_type',
    'title',
    'is_read',
    'email_sent',
    'email_sent_at',
    'created_at',
  )
  list_filter = (
    'notification_type',
    'is_read',
    'email_sent',
    'created_at',
  )
  search_fields = (
    'recipient__username',
    'recipient__email',
    'title',
    'message',
  )
  readonly_fields = ('created_at', 'email_sent_at', 'formatted_metadata')
  raw_id_fields = ('recipient', 'actor')
  date_hierarchy = 'created_at'
  ordering = ('-created_at',)

  fieldsets = (
    (
      None,
      {
        'fields': (
          'recipient',
          'actor',
          'notification_type',
          'title',
          'message',
          'url',
          'is_read',
        )
      },
    ),
    (
      'Email delivery',
      {
        'fields': ('email_sent', 'email_sent_at'),
      },
    ),
    (
      'Metadata',
      {
        'fields': ('formatted_metadata', 'created_at'),
      },
    ),
  )

  @admin.display(description='Metadata')
  def formatted_metadata(self, obj):
    if not obj.metadata:
      return '-'
    return format_html('<pre style="white-space: pre-wrap;">{}</pre>', obj.metadata)


@admin.register(NotificationPreference)
class NotificationPreferenceAdmin(admin.ModelAdmin):
  list_display = (
    'user',
    'askme_emails',
    'ad_emails',
    'favorite_notifications',
    'community_notifications',
    'weekly_digest',
    'comment_notifications',
    'updated_at',
  )
  list_filter = (
    'askme_emails',
    'ad_emails',
    'favorite_notifications',
    'community_notifications',
    'weekly_digest',
    'comment_notifications',
  )
  search_fields = ('user__username', 'user__email')
  raw_id_fields = ('user',)
