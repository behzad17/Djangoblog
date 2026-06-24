from .services import NotificationService


def notification_counts(request):
    if request.user.is_authenticated:
        return {
            'unread_notification_count': NotificationService.get_unread_count(
                request.user
            ),
        }
    return {'unread_notification_count': 0}
