"""
Admin statistics context for admin index page.
Provides pending items counts including pro ad requests.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.utils import timezone
from datetime import timedelta


def get_admin_stats():
    """
    Get statistics for admin dashboard.
    Returns a dictionary with counts of pending items.
    All errors are caught to prevent breaking the admin panel.
    """
    stats = {
        'pending_posts': 0,
        'pending_ads': 0,
        'pending_questions': 0,
        'pending_comments': 0,
        'pending_urls': 0,
        'recent_expert_posts': 0,
        'pending_pro_requests': 0,  # New: Pro ad requests
    }
    
    try:
        from blog.models import Post, Comment
        from ads.models import Ad
        from askme.models import Question
        
        # Get pending posts (draft status)
        try:
            stats['pending_posts'] = Post.objects.filter(status=0).count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting pending posts: {e}", exc_info=True)
        
        # Get pending ads
        try:
            stats['pending_ads'] = Ad.objects.filter(is_approved=False).count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting pending ads: {e}", exc_info=True)
        
        # Get pending pro ad requests (Free ads with pro_requested=True)
        try:
            stats['pending_pro_requests'] = Ad.objects.filter(
                plan='free',
                pro_requested=True
            ).count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting pending pro requests: {e}", exc_info=True)
        
        # Get pending URLs
        try:
            pending_urls_ads = Ad.objects.filter(
                url_approved=False,
                is_approved=True
            ).count()
            pending_urls_posts = Post.objects.filter(
                url_approved=False,
                status=1,
                external_url__isnull=False
            ).exclude(slug='').exclude(slug__isnull=True).count()
            stats['pending_urls'] = pending_urls_ads + pending_urls_posts
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting pending URLs: {e}", exc_info=True)
        
        # Get pending questions
        try:
            stats['pending_questions'] = Question.objects.filter(answered=False).count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting pending questions: {e}", exc_info=True)
        
        # Get pending comments
        try:
            stats['pending_comments'] = Comment.objects.filter(approved=False).count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting pending comments: {e}", exc_info=True)
        
        # Get recent expert posts (last 24 hours)
        try:
            from django.contrib.auth.models import User
            expert_users = User.objects.filter(
                profile__can_publish_without_approval=True
            ).values_list('id', flat=True)
            stats['recent_expert_posts'] = Post.objects.filter(
                status=1,
                author_id__in=expert_users,
                created_on__gte=timezone.now() - timedelta(days=1)
            ).exclude(slug='').exclude(slug__isnull=True).count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting recent expert posts: {e}", exc_info=True)
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting admin stats: {e}", exc_info=True)
    
    return stats

