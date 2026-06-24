from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .models import Notification
from .services import NotificationService


@login_required
def notification_dropdown(request):
    notifications = list(NotificationService.get_recent(request.user, limit=10))
    unread_count = NotificationService.get_unread_count(request.user)
    return render(
        request,
        'notifications/dropdown_partial.html',
        {
            'notifications': notifications,
            'unread_count': unread_count,
        },
    )


@login_required
def notification_list(request):
    notifications_qs = (
        Notification.objects.filter(recipient=request.user)
        .select_related('actor')
        .order_by('-created_at')
    )
    paginator = Paginator(notifications_qs, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(
        request,
        'notifications/list.html',
        {
            'page_obj': page_obj,
            'notifications': page_obj.object_list,
            'unread_count': NotificationService.get_unread_count(request.user),
        },
    )


@login_required
@require_POST
def mark_notification_read(request, notification_id):
    success = NotificationService.mark_read(notification_id, request.user)
    return JsonResponse(
        {
            'success': success,
            'unread_count': NotificationService.get_unread_count(request.user),
        }
    )


@login_required
@require_POST
def mark_all_notifications_read(request):
    marked_count = NotificationService.mark_all_read(request.user)
    return JsonResponse(
        {
            'success': True,
            'marked_count': marked_count,
            'unread_count': 0,
        }
    )
