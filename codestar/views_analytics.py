"""
Analytics dashboard view for staff members.
Shows aggregated view counts for posts and ads.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Sum, Count
from blog.models import PostViewCount, Post
from ads.models import AdsViewCount, Ad
from django.urls import reverse


def staff_required(user):
    """Check if user is staff."""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(staff_required)
def analytics_dashboard(request):
    """
    Staff-only analytics dashboard showing view statistics.
    
    Displays:
    - Summary stats (total views, counts)
    - Top 10 posts by total_views
    - Top 10 ads by total_views
    """
    # Summary statistics
    post_stats = PostViewCount.objects.aggregate(
        total_post_views=Sum('total_views'),
        posts_with_views=Count('id', distinct=True)
    )
    
    ad_stats = AdsViewCount.objects.aggregate(
        total_ad_views=Sum('total_views'),
        ads_with_views=Count('id', distinct=True)
    )
    
    # Top 10 posts by total_views
    top_posts = (
        PostViewCount.objects
        .select_related('post')
        .order_by('-total_views')[:10]
    )
    
    # Top 10 ads by total_views
    top_ads = (
        AdsViewCount.objects
        .select_related('ad')
        .order_by('-total_views')[:10]
    )
    
    context = {
        'total_post_views': post_stats['total_post_views'] or 0,
        'posts_with_views': post_stats['posts_with_views'] or 0,
        'total_ad_views': ad_stats['total_ad_views'] or 0,
        'ads_with_views': ad_stats['ads_with_views'] or 0,
        'top_posts': top_posts,
        'top_ads': top_ads,
    }
    
    return render(request, 'dashboard/analytics.html', context)

