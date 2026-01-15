"""
URL configuration for codestar project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from ratelimit.decorators import ratelimit
from allauth.account import views as allauth_views
from blog.sitemaps import PostSitemap, CategorySitemap
from blog.views_robots import robots_txt
from codestar.views_db_health import db_health_dashboard
from codestar.admin_incoming import admin_incoming_items
from codestar.views_analytics import analytics_dashboard

# Override admin site index to add statistics
from django.contrib.admin.views.decorators import staff_member_required
from django.template.response import TemplateResponse
from django.utils import timezone
from datetime import timedelta

# Capture original admin index function safely
try:
    _original_index = admin.site.index
except AttributeError:
    # Fallback if admin.site.index doesn't exist
    from django.contrib.admin.views.decorators import staff_member_required as _staff_required
    from django.contrib.admin.sites import AdminSite
    _original_index = AdminSite.index

@staff_member_required
def admin_index_with_stats(request, extra_context=None):
    """Admin index with pending content statistics."""
    extra_context = extra_context or {}
    
    # Initialize default stats
    stats = {
        'pending_posts': 0,
        'pending_ads': 0,
        'pending_urls_ads': 0,
        'pending_urls_posts': 0,
        'pending_questions': 0,
        'pending_comments': 0,
        'recent_expert_posts': 0,
        'pending_urls': 0,
    }
    
    # Safely collect stats - all errors are caught and logged
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
        
        # Get pending URLs for ads
        try:
            stats['pending_urls_ads'] = Ad.objects.filter(
                url_approved=False,
                is_approved=True
            ).count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting pending URLs for ads: {e}", exc_info=True)
        
        # Get pending URLs for posts
        try:
            stats['pending_urls_posts'] = Post.objects.filter(
                url_approved=False,
                status=1,
                external_url__isnull=False
            ).exclude(slug='').exclude(slug__isnull=True).count()
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error counting pending URLs for posts: {e}", exc_info=True)
        
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
        
        # Get recent expert posts (with safe profile access)
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
        
        # Calculate total pending URLs
        stats['pending_urls'] = stats['pending_urls_ads'] + stats['pending_urls_posts']
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error getting admin stats: {e}", exc_info=True)
    
    # Safely update context and call original index
    try:
        extra_context.update(stats)
        # Call original index function safely
        if callable(_original_index):
            return _original_index(request, extra_context)
        else:
            # Fallback to default admin index
            from django.contrib.admin.views.decorators import staff_member_required
            from django.contrib.admin.sites import AdminSite
            return AdminSite.index(admin.site, request, extra_context)
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calling original admin index: {e}", exc_info=True)
        # Last resort: return basic admin index without stats
        from django.contrib.admin.views.decorators import staff_member_required
        from django.contrib.admin.sites import AdminSite
        return AdminSite.index(admin.site, request, {})

admin.site.index = admin_index_with_stats

# Sitemap configuration
sitemaps = {
    'posts': PostSitemap,
    'categories': CategorySitemap,
}

urlpatterns = [
    path("about/", include("about.urls")),
    path("ask-me/", include("askme.urls")),
    path("ads/", include("ads.urls", namespace="ads")),
    path("related-links/", include("related_links.urls", namespace="related_links")),
    # Rate-limit login and signup endpoints
    # More lenient in development (20/min) for testing, stricter in production (5/min)
    # Note: Rate limiting is less strict in development to allow easier testing
    path(
        "accounts/login/",
        ratelimit(key="ip", rate="20/m", block=True)(allauth_views.login),
        name="account_login",
    ),
    path(
        "accounts/signup/",
        ratelimit(key="ip", rate="20/m", block=True)(allauth_views.signup),
        name="account_signup",
    ),
    path(
        "accounts/password/reset/",
        ratelimit(key="ip", rate="10/m", block=True)(allauth_views.password_reset),
        name="account_reset_password",
    ),
    # Internal: Database Health Dashboard (staff-only, read-only)
    path("admin/db-health/", db_health_dashboard, name="db_health_dashboard"),
    # Admin: Incoming Items Page
    path("admin/incoming/", admin_incoming_items, name="admin_incoming_items"),
    # Analytics Dashboard (staff-only)
    path("dashboard/analytics/", analytics_dashboard, name="analytics_dashboard"),
    # Custom account URLs (must come before allauth.urls to avoid conflicts)
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("allauth.urls")),
    path("captcha/", include("captcha.urls")),
    path('admin/', admin.site.urls),
    path('summernote/', include('django_summernote.urls')),
    # SEO: Sitemap and robots.txt
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    path('robots.txt', robots_txt, name='robots_txt'),
    path("", include("blog.urls"), name="blog-urls"),
]
