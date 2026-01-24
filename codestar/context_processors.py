"""
Context processor for admin panel statistics.
This safely provides stats to admin templates without overriding admin views.
"""
from django.contrib.admin.views.decorators import staff_member_required


def admin_stats(request):
    """
    Context processor that adds admin statistics to template context.
    Only active when user is staff and on admin pages.
    """
    # Only add stats for admin pages and staff users
    if not request.path.startswith('/admin/') or not hasattr(request, 'user') or not request.user.is_staff:
        return {}
    
    try:
        from codestar.admin_stats import get_admin_stats
        return get_admin_stats()
    except Exception:
        # Silently return empty dict if there's any error
        # This prevents breaking the admin panel
        return {
            'pending_posts': 0,
            'pending_ads': 0,
            'pending_questions': 0,
            'pending_comments': 0,
            'pending_urls': 0,
            'recent_expert_posts': 0,
            'pending_pro_requests': 0,
        }

