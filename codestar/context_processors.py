"""
Context processor for admin panel statistics.
This safely provides stats to admin templates without overriding admin views.
"""
import logging

logger = logging.getLogger(__name__)


def admin_stats(request):
    """
    Context processor that adds admin statistics to template context.
    Only active when user is staff and on admin pages.
    """
    # Only add stats for admin pages
    try:
        if not request.path.startswith('/admin/'):
            return default_stats
        
        # Check if user is authenticated and staff (safely)
        if not hasattr(request, 'user'):
            return default_stats
        
        try:
            is_staff = request.user.is_authenticated and request.user.is_staff
        except (AttributeError, TypeError):
            is_staff = False
        
        if not is_staff:
            return default_stats
    except Exception as e:
        logger.error(f"Error checking admin access: {e}", exc_info=True)
        return default_stats
    
    # Return default empty stats - will be populated if get_admin_stats works
    default_stats = {
        'pending_posts': 0,
        'pending_ads': 0,
        'pending_questions': 0,
        'pending_comments': 0,
        'pending_urls': 0,
        'recent_expert_posts': 0,
        'pending_pro_requests': 0,
    }
    
    # Try to get actual stats, but return defaults if anything fails
    try:
        from codestar.admin_stats import get_admin_stats
        stats = get_admin_stats()
        # Ensure all required keys exist
        for key in default_stats.keys():
            if key not in stats:
                stats[key] = 0
        return stats
    except Exception as e:
        # Log error but don't break the admin panel
        logger.error(f"Error in admin_stats context processor: {e}", exc_info=True)
        return default_stats

