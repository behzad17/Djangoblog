"""
Admin view for incoming items - unified view of all pending content.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta


@staff_member_required
def admin_incoming_items(request):
    """Unified view of all pending content requiring admin review."""
    from blog.models import Post, Comment
    from ads.models import Ad
    from askme.models import Question
    
    # Get all pending items (limited to 20 per section for performance)
    pending_posts = Post.objects.filter(status=0).exclude(slug='').exclude(slug__isnull=True).select_related(
        'author', 'category'
    ).order_by('-created_on')[:20]
    
    pending_ads = Ad.objects.filter(
        is_approved=False
    ).select_related('owner', 'category').order_by('-created_on')[:20]
    
    pending_urls_ads = Ad.objects.filter(
        url_approved=False,
        is_approved=True  # Only show if ad is approved
    ).select_related('owner', 'category')[:20]
    
    pending_urls_posts = Post.objects.filter(
        url_approved=False,
        status=1,  # Only show if post is published
        external_url__isnull=False
    ).exclude(slug='').exclude(slug__isnull=True).select_related('author', 'category')[:20]
    
    pending_questions = Question.objects.filter(
        answered=False
    ).select_related('user', 'moderator').order_by('-created_on')[:20]
    
    pending_comments = Comment.objects.filter(
        approved=False
    ).select_related('author', 'post').order_by('-created_on')[:20]
    
    # Recent expert posts (last 24 hours)
    recent_expert_posts = Post.objects.filter(
        status=1,
        author__profile__can_publish_without_approval=True,
        created_on__gte=timezone.now() - timedelta(days=1)
    ).exclude(slug='').exclude(slug__isnull=True).select_related('author', 'category').order_by('-created_on')[:20]
    
    # Statistics
    stats = {
        'total_pending_posts': Post.objects.filter(status=0).count(),
        'total_pending_ads': Ad.objects.filter(is_approved=False).count(),
        'total_pending_urls': (
            Ad.objects.filter(url_approved=False).count() +
            Post.objects.filter(url_approved=False).count()
        ),
        'total_pending_questions': Question.objects.filter(answered=False).count(),
        'total_pending_comments': Comment.objects.filter(approved=False).count(),
        'recent_expert_posts_count': recent_expert_posts.count(),
    }
    
    return render(request, 'admin/incoming_items.html', {
        'pending_posts': pending_posts,
        'pending_ads': pending_ads,
        'pending_urls_ads': pending_urls_ads,
        'pending_urls_posts': pending_urls_posts,
        'pending_questions': pending_questions,
        'pending_comments': pending_comments,
        'recent_expert_posts': recent_expert_posts,
        'stats': stats,
    })

