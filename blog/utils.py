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
    
    # Create page view record with error handling
    try:
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
    except Exception as e:
        # Log database errors but don't break the page
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating page view record: {e}", exc_info=True)
        return None
    
    # Update aggregated view count (async or via signal)
    # Wrap in try-except to prevent signal errors from breaking tracking
    if post:
        try:
            from .signals import update_post_view_count
            if hasattr(update_post_view_count, 'delay'):
                update_post_view_count.delay(post.id)
            else:
                update_post_view_count(post.id)
        except (ImportError, AttributeError):
            # Signal function doesn't exist, skip update (this is OK)
            pass
        except Exception as e:
            # Log signal errors but don't break tracking
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error updating post view count for post {post.id}: {e}", exc_info=True)
    
    return page_view


# Reading Time and TOC (Table of Contents) Utilities
def compute_reading_time(content_html):
    """
    Calculate reading time in minutes from HTML content.
    
    Args:
        content_html: HTML string containing the post content
        
    Returns:
        int: Reading time in minutes (minimum 1)
    """
    if not content_html:
        return 1
    
    # Strip HTML tags to get plain text
    # Simple regex to remove HTML tags (safe for sanitized content)
    text = re.sub(r'<[^>]+>', ' ', content_html)
    
    # Remove extra whitespace and split into words
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Split by whitespace (works for both Persian and English)
    words = text.split()
    word_count = len(words)
    
    # Calculate reading time: ~200 words per minute
    # Minimum 1 minute
    reading_time = max(1, round(word_count / 200))
    
    return reading_time


def build_toc_and_anchors(content_html):
    """
    Extract headings from HTML and generate TOC with anchor IDs.
    
    Args:
        content_html: HTML string containing the post content
        
    Returns:
        tuple: (toc_items, updated_html)
            - toc_items: List of dicts with {level: int, title: str, anchor: str}
            - updated_html: HTML with anchor IDs added to headings
    """
    if not content_html:
        return [], content_html
    
    toc_items = []
    updated_html = content_html
    heading_counter = {}
    
    # Pattern to match h2 and h3 tags
    # Match: <h2>Title</h2> or <h3>Title</h3>
    pattern = r'<(h[23])[^>]*>(.*?)</\1>'
    
    def replace_heading(match):
        """Replace heading with version that includes anchor ID."""
        tag = match.group(1)  # h2 or h3
        title = match.group(2).strip()
        
        # Remove any HTML inside the heading title (keep only text)
        title_text = re.sub(r'<[^>]+>', '', title)
        
        if not title_text:
            return match.group(0)  # Return original if no text
        
        # Generate unique anchor ID
        base_slug = slugify(title_text, allow_unicode=True)
        if not base_slug:
            base_slug = 'section'
        
        # Ensure uniqueness
        if base_slug in heading_counter:
            heading_counter[base_slug] += 1
            anchor = f"{base_slug}-{heading_counter[base_slug]}"
        else:
            heading_counter[base_slug] = 0
            anchor = base_slug
        
        # Extract level (2 or 3)
        level = int(tag[1])
        
        # Add to TOC
        toc_items.append({
            'level': level,
            'title': title_text,
            'anchor': anchor
        })
        
        # Return heading with anchor ID
        # Reconstruct the opening tag properly
        full_match = match.group(0)
        # Find where the title content starts (after the closing > of opening tag)
        title_start = full_match.find('>') + 1
        # Find where the title content ends (before the closing </tag>)
        title_end = full_match.rfind(f'</{tag}>')
        
        # Extract the opening tag (everything before the title)
        opening_tag = full_match[:title_start]
        
        # Add or replace ID attribute
        if 'id=' in opening_tag:
            # If ID already exists, replace it
            opening_tag = re.sub(r'id="[^"]*"', f'id="{anchor}"', opening_tag)
        else:
            # Add ID attribute before the closing >
            opening_tag = opening_tag.rstrip('>') + f' id="{anchor}">'
        
        # Return the reconstructed heading with anchor ID
        return f'{opening_tag}{title}</{tag}>'
    
    # Process all headings
    updated_html = re.sub(pattern, replace_heading, updated_html, flags=re.IGNORECASE | re.DOTALL)
    
    return toc_items, updated_html


def should_show_toc(content_html, toc_items, min_headings=3, min_words=600):
    """
    Determine if TOC should be displayed.
    
    Args:
        content_html: HTML string containing the post content
        toc_items: List of TOC items
        min_headings: Minimum number of headings required
        min_words: Minimum word count required (if headings < min_headings)
        
    Returns:
        bool: True if TOC should be shown
    """
    # Must have at least some headings
    if len(toc_items) < min_headings:
        # Check word count as alternative
        text = re.sub(r'<[^>]+>', ' ', content_html)
        text = re.sub(r'\s+', ' ', text).strip()
        word_count = len(text.split())
        
        # Show TOC if content is long enough even with fewer headings
        if word_count < min_words:
            return False
    
    return True


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
