"""
Account views for user account management.
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from blog.models import Post
from notifications.forms import NotificationPreferenceForm
from notifications.services import NotificationService


@login_required
@require_http_methods(['GET', 'POST'])
def account_settings(request):
    """
    Account settings page: password/email links, notification preferences,
    and the user's published posts.
    """
    preferences = NotificationService.get_or_create_preferences(request.user)
    notification_form = NotificationPreferenceForm(instance=preferences)

    if request.method == 'POST' and request.POST.get('form_type') == 'notification_preferences':
        notification_form = NotificationPreferenceForm(
            request.POST,
            instance=preferences,
        )
        if notification_form.is_valid():
            notification_form.save()
            messages.success(request, 'تنظیمات اعلان‌ها ذخیره شد.')
            return redirect('account_settings')

    # Get user's published posts (status=1, not soft-deleted)
    user_posts = Post.objects.filter(
        author=request.user,
        status=1,  # Published
        is_deleted=False  # Not soft-deleted
    ).select_related('category').order_by('-created_on')

    # Paginate (15 items per page)
    paginator = Paginator(user_posts, 15)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'account/settings.html', {
        'notification_form': notification_form,
        'user_posts': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    })
