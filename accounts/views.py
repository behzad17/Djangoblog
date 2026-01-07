"""
Account views for user account management.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.core.paginator import Paginator
from blog.models import Post


@login_required
def account_settings(request):
    """
    Account settings page that provides links to change password and email,
    and displays user's published posts.
    """
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
        'user_posts': page_obj,
        'is_paginated': page_obj.has_other_pages(),
    })
