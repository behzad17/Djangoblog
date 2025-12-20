"""
Utility functions for page view tracking.
Includes privacy-compliant anonymization and bot detection.
"""
import hashlib
import re
from django.utils import timezone
from datetime import timedelta
from .models import PageView, PostViewCount


def anonymize_ip(ip_address):
    """
    Hash IP address for privacy (SHA256).
    Returns first 16 characters for indexing efficiency.
    
    Args:
        ip_address: The IP address to anonymize
        
    Returns:
        str: Hashed IP address (first 16 chars) or None
    """
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode()).hexdigest()[:16]


def anonymize_user_agent(user_agent):
    """
    Hash user agent for privacy.
    
    Args:
        user_agent: The user agent string to anonymize
        
    Returns:
        str: Hashed user agent (first 16 chars) or None
    """
    if not user_agent:
        return None
    return hashlib.sha256(user_agent.encode()).hexdigest()[:16]


def is_bot_request(user_agent, ip_address=None):
    """
    Detect common bots and crawlers.
    
    Args:
        user_agent: The HTTP User-Agent header
        ip_address: Optional IP address (for future IP-based bot detection)
        
    Returns:
        bool: True if request appears to be from a bot
    """
    if not user_agent:
        return True
    
    bot_patterns = [
        r'bot', r'crawler', r'spider', r'scraper',
        r'googlebot', r'bingbot', r'slurp', r'duckduckbot',
        r'baiduspider', r'yandexbot', r'sogou', r'exabot',
        r'facebookexternalhit', r'twitterbot', r'rogerbot',
        r'linkedinbot', r'embedly', r'quora', r'pinterest',
        r'slackbot', r'applebot', r'flipboard', r'tumblr',
        r'bitlybot', r'vkShare', r'W3C_Validator',
        r'python-requests', r'curl', r'wget', r'postman',
        r'Go-http-client', r'Java/', r'Apache-HttpClient',
        r'AhrefsBot', r'SemrushBot', r'MJ12bot',
    ]
    
    user_agent_lower = user_agent.lower()
    for pattern in bot_patterns:
        if re.search(pattern, user_agent_lower):
            return True
    
    return False


def get_client_ip(request):
    """
    Get client IP address from request, handling proxies.
    
    Args:
        request: Django HttpRequest object
        
    Returns:
        str: Client IP address
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def track_page_view(request, post=None, url_path=None):
    """
    Track a page view for a post or URL with deduplication.
    
    This function handles:
    - Bot filtering
    - Privacy-compliant data anonymization
    - Rate limiting (prevents duplicate counting)
    - View count cache updates
    
    Args:
        request: Django HttpRequest object
        post: Post object (if tracking a post view)
        url_path: URL path string (if tracking a non-post page)
        
    Returns:
        bool: True if view was tracked, False if skipped (duplicate/bot)
    """
    # Get request metadata
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    
    # Skip bots
    if is_bot_request(user_agent, ip_address):
        return False
    
    # Anonymize for privacy
    ip_hash = anonymize_ip(ip_address)
    user_agent_hash = anonymize_user_agent(user_agent)
    session_key = request.session.session_key or ''
    
    # Use post slug or provided url_path
    if post:
        path = f'/blog/{post.slug}/'
    elif url_path:
        path = url_path
    else:
        path = request.path
    
    # Rate limiting: check for recent view (1 hour window)
    cutoff_time = timezone.now() - timedelta(hours=1)
    
    # Check session-based duplicate
    if session_key and post:
        if PageView.objects.filter(
            post=post,
            session_key=session_key,
            viewed_at__gte=cutoff_time
        ).exists():
            return False
    
    # Check IP+UA-based duplicate (fallback for users without sessions)
    if ip_hash and user_agent_hash and post:
        if PageView.objects.filter(
            post=post,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
            viewed_at__gte=cutoff_time
        ).exists():
            return False
    
    # Create view record
    PageView.objects.create(
        post=post,
        url_path=path,
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key,
        ip_hash=ip_hash,
        user_agent_hash=user_agent_hash,
        referer=request.META.get('HTTP_REFERER', ''),
        is_bot=False,
    )
    
    # Update cache (consider doing this asynchronously for high-traffic sites)
    if post:
        update_view_count_cache(post)
    
    return True


def update_view_count_cache(post):
    """
    Update aggregated view count cache for a post.
    
    For high-traffic sites, consider calling this asynchronously
    (e.g., via Celery or Django-Q).
    
    Args:
        post: Post object to update counts for
    """
    view_count, _ = PostViewCount.objects.get_or_create(post=post)
    view_count.total_views = PageView.objects.filter(
        post=post, is_bot=False
    ).count()
    view_count.unique_views = PageView.objects.filter(
        post=post, is_bot=False
    ).values('session_key', 'ip_hash', 'user_agent_hash').distinct().count()
    view_count.save()

