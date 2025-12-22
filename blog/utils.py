from django.db.models import Count, Q
from django.shortcuts import (
    render,
    get_object_or_404,
    reverse,
    redirect,
)
from django.views import generic
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from ratelimit.decorators import ratelimit
from django.utils.text import slugify
import json
import hashlib
import re
from django.utils import timezone
from django.core.cache import cache
import bleach

from .models import Post, Comment, Favorite, Category, Like, PageView

# Bot detection patterns
BOT_PATTERNS = [
    r'bot', r'crawler', r'spider', r'scraper', r'curl', r'wget',
    r'python-requests', r'go-http-client', r'java/', r'httpclient',
    r'apache-httpclient', r'okhttp', r'postman', r'insomnia',
    r'headless', r'phantom', r'selenium', r'puppeteer'
]

def get_client_ip(request):
    """
    Get the client's IP address from request headers.
    Handles proxy/load balancer scenarios.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def hash_ip(ip):
    """Hash IP address for privacy compliance."""
    if not ip:
        return None
    return hashlib.sha256(ip.encode()).hexdigest()

def hash_user_agent(user_agent):
    """Hash user agent string for privacy compliance."""
    if not user_agent:
        return None
    return hashlib.sha256(user_agent.encode()).hexdigest()

def is_bot(user_agent):
    """Detect if request is from a bot/crawler."""
    if not user_agent:
        return False
    user_agent_lower = user_agent.lower()
    for pattern in BOT_PATTERNS:
        if re.search(pattern, user_agent_lower):
            return True
    return False

def track_page_view(request, post=None, url_path=None):
    """
    Track a page view with privacy-compliant anonymization.
    
    This function:
    - Hashes IP and user agent (doesn't store raw PII)
    - Filters out bots
    - Deduplicates views using session + IP + user agent hash
    - Updates aggregated view counts
    """
    # Skip tracking for bots
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    if is_bot(user_agent):
        return
    
    # Get anonymized tracking data
    ip = get_client_ip(request)
    ip_hash = hash_ip(ip)
    user_agent_hash = hash_user_agent(user_agent)
    session_key = request.session.session_key
    
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    # Determine what was viewed
    if post:
        url_path = post.get_absolute_url() if hasattr(post, 'get_absolute_url') else f'/{post.slug}/'
    elif not url_path:
        url_path = request.path
    
    # Create deduplication key
    dedup_key = f"view:{session_key}:{ip_hash}:{user_agent_hash}:{url_path}"
    
    # Check cache to avoid duplicate tracking in same session
    cache_key = f"pageview_dedup:{dedup_key}"
    if cache.get(cache_key):
        return  # Already tracked in this session
    
    # Set cache for 1 hour to prevent duplicate tracking
    cache.set(cache_key, True, 3600)
    
    # Create page view record
    page_view = PageView.objects.create(
        post=post,
        url_path=url_path,
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key,
        ip_hash=ip_hash,
        user_agent_hash=user_agent_hash,
        referer=request.META.get('HTTP_REFERER', '')[:500] if request.META.get('HTTP_REFERER') else '',
        is_bot=False
    )
    
    # Update aggregated view count (async or via signal)
    if post:
        from .signals import update_post_view_count
        update_post_view_count.delay(post.id) if hasattr(update_post_view_count, 'delay') else update_post_view_count(post.id)
    
    return page_view


# HTML Sanitization for XSS Prevention
# Allowed tags and attributes for rich text content
ALLOWED_TAGS = [
    'p', 'br', 'strong', 'em', 'u', 'b', 'i', 's', 'strike',
    'ul', 'ol', 'li', 'a', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'div', 'span', 'pre', 'code', 'hr', 'sub', 'sup'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'div': ['class'],
    'span': ['class'],
    'p': ['class'],
    'h1': ['class'], 'h2': ['class'], 'h3': ['class'],
    'h4': ['class'], 'h5': ['class'], 'h6': ['class'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

ALLOWED_STYLES = []  # No inline styles allowed for security


def sanitize_html(content):
    """
    Sanitize HTML content to prevent XSS attacks.
    
    Removes:
    - Script tags and event handlers (onclick, onerror, etc.)
    - Inline JavaScript (javascript: URLs)
    - Iframes and other dangerous elements
    - Inline styles (unless configured)
    
    Allows:
    - Basic formatting tags (p, strong, em, etc.)
    - Safe links (http/https/mailto)
    - Lists and headings
    """
    if not content:
        return ''
    
    # Sanitize HTML content
    cleaned = bleach.clean(
        content,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True  # Strip disallowed tags instead of escaping
    )
    
    # Additional safety: Remove any remaining javascript: URLs
    cleaned = re.sub(r'javascript:', '', cleaned, flags=re.IGNORECASE)
    
    return cleaned
