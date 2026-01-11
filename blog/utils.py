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
    try:
        if not content_html:
            return 1
        
        # Ensure content_html is a string
        if not isinstance(content_html, str):
            content_html = str(content_html)
        
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
    except Exception as e:
        # If anything fails, return default reading time
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error calculating reading time: {e}", exc_info=True)
        return 1


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
        return [], content_html or ''
    
    # Ensure content_html is a string
    if not isinstance(content_html, str):
        content_html = str(content_html)
    
    toc_items = []
    updated_html = content_html
    heading_counter = {}
    
    # Pattern to match h2 and h3 tags with any attributes
    # Match: <h2>Title</h2> or <h3 class="something">Title</h3>
    pattern = r'<(h[23])([^>]*)>(.*?)</\1>'
    
    def replace_heading(match):
        """Replace heading with version that includes anchor ID."""
        try:
            tag = match.group(1)  # h2 or h3
            attrs = match.group(2)  # existing attributes (if any)
            title = match.group(3).strip()  # title content
            
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
            
            # Build new opening tag with ID
            # Check if ID already exists in attributes
            attrs = attrs.strip()
            if 'id=' in attrs:
                # Replace existing ID
                new_attrs = re.sub(r'id="[^"]*"', f'id="{anchor}"', attrs)
            else:
                # Add ID attribute
                if attrs:
                    new_attrs = attrs + f' id="{anchor}"'
                else:
                    new_attrs = f'id="{anchor}"'
            
            # Return the reconstructed heading with anchor ID
            # Handle spacing correctly
            if new_attrs:
                return f'<{tag} {new_attrs}>{title}</{tag}>'
            else:
                return f'<{tag}>{title}</{tag}>'
        except Exception:
            # If anything goes wrong, return original
            return match.group(0)
    
    # Process all headings
    try:
        updated_html = re.sub(pattern, replace_heading, updated_html, flags=re.IGNORECASE | re.DOTALL)
    except Exception as e:
        # If regex fails, return original content
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error processing headings in build_toc_and_anchors: {e}", exc_info=True)
        updated_html = content_html
    
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
    'div', 'span', 'pre', 'code', 'hr', 'sub', 'sup',
    'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'div': ['class'],
    'span': ['class'],
    'p': ['class'],
    'h1': ['class'], 'h2': ['class'], 'h3': ['class'],
    'h4': ['class'], 'h5': ['class'], 'h6': ['class'],
    'img': ['src', 'alt', 'title', 'width', 'height', 'class'],
    'table': ['class', 'border', 'cellpadding', 'cellspacing'],
    'thead': ['class'],
    'tbody': ['class'],
    'tr': ['class'],
    'th': ['class', 'colspan', 'rowspan'],
    'td': ['class', 'colspan', 'rowspan'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']

ALLOWED_STYLES = []  # No inline styles allowed for security


def convert_plain_text_to_html(text):
    """
    Convert plain text with newlines to HTML paragraphs.
    
    This handles content stored as plain text (e.g., from Summernote
    when it wasn't configured to submit HTML, or legacy posts).
    
    Security: This function does NOT escape content - bleach.clean() will handle
    all XSS prevention when the HTML is sanitized.
    
    Args:
        text: Plain text string with newline characters
        
    Returns:
        HTML string with paragraphs wrapped in <p> tags, or original text if already HTML
    """
    if not text:
        return ''
    
    # Check if content already contains HTML tags
    # Look for common HTML tags: <p>, <div>, <br>, <strong>, <em>, <h1-h6>, <ul>, <ol>, <li>, etc.
    # If HTML tags are found, assume content is already HTML and return as-is
    html_tag_pattern = r'<[a-z]+[^>]*>|</[a-z]+>'
    if re.search(html_tag_pattern, text, re.IGNORECASE):
        return text
    
    # Content is plain text - convert to HTML
    # Normalize line endings (handle \r\n, \r, \n)
    text = re.sub(r'\r\n|\r', '\n', text)
    
    # Split by double newlines (paragraph breaks)
    # This creates natural paragraph boundaries
    paragraphs = re.split(r'\n\s*\n+', text)
    
    # Process each paragraph
    html_paragraphs = []
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        
        # Replace single newlines within paragraph with <br>
        # This preserves intentional line breaks within paragraphs
        para = para.replace('\n', '<br>')
        
        # Wrap in paragraph tag
        # Note: We don't escape here - bleach.clean() will handle XSS prevention
        html_paragraphs.append(f'<p>{para}</p>')
    
    # If no paragraphs were created (single line with no double newlines), wrap entire content
    if not html_paragraphs:
        text = text.strip()
        if text:
            # Replace newlines with <br> for single-line content
            text = text.replace('\n', '<br>')
            html_paragraphs.append(f'<p>{text}</p>')
    
    return '\n'.join(html_paragraphs)


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
    
    Also normalizes HTML structure:
    - Converts plain text to HTML paragraphs if content is plain text
    - Converts div tags containing text to p tags for better paragraph display
    - Ensures proper paragraph structure
    """
    if not content:
        return ''
    
    # CRITICAL FIX: Convert plain text to HTML if content has no HTML tags
    # This handles legacy posts stored as plain text
    content = convert_plain_text_to_html(content)
    
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
    
    # Normalize HTML structure: Convert div tags to p tags for better paragraph display
    # This handles cases where Summernote saves content with div tags instead of p tags
    # Only convert divs that don't have specific classes (like those used for formatting)
    # Pattern: <div>text content</div> -> <p>text content</p>
    # But preserve divs with classes (they might be used for special formatting)
    def normalize_div_to_p(match):
        attrs = match.group(1) or ''
        div_content = match.group(2) or ''
        # Check if div has class attribute (might be used for formatting)
        if attrs.strip() and 'class=' in attrs:
            # Keep div if it has a class (might be intentional formatting)
            return match.group(0)
        # Convert simple divs to paragraphs
        return f'<p>{div_content}</p>'
    
    # Convert <div>text</div> to <p>text</p> (but preserve divs with classes)
    # Use DOTALL flag to match content across multiple lines
    cleaned = re.sub(
        r'<div([^>]*)>(.*?)</div>',
        normalize_div_to_p,
        cleaned,
        flags=re.IGNORECASE | re.DOTALL
    )
    
    # Remove empty divs
    cleaned = re.sub(r'<div[^>]*>\s*</div>', '', cleaned, flags=re.IGNORECASE)
    
    # Normalize multiple consecutive <br> tags to paragraph breaks
    # Replace <br><br> or <br/><br/> with paragraph breaks
    cleaned = re.sub(r'(<br\s*/?>\s*){2,}', '</p><p>', cleaned, flags=re.IGNORECASE)
    
    return cleaned


# Comment Moderation Utilities
def is_trusted_commenter(user):
    """
    Check if user has 5+ approved comments (trusted commenter).
    
    Args:
        user: User instance
        
    Returns:
        bool: True if user has 5 or more approved comments
    """
    if not user or not user.is_authenticated:
        return False
    
    approved_count = Comment.objects.filter(
        author=user,
        approved=True
    ).count()
    
    return approved_count >= 5


def contains_link(text):
    """
    Check if text contains any URL pattern.
    
    Detects:
    - http:// and https:// URLs
    - www. URLs
    - Common domain extensions (.com, .org, .net, .io, .se, .ir)
    
    Args:
        text: Text to check
        
    Returns:
        bool: True if text contains a link pattern
    """
    if not text:
        return False
    
    text_lower = text.lower()
    
    # Link patterns
    link_patterns = [
        r'https?://\S+',  # http:// or https://
        r'www\.\S+',      # www.example.com
        r'\S+\.(com|org|net|io|se|ir|co|uk|de|fr|es|it|nl|be|dk|fi|no|pl|cz|at|ch|au|ca|jp|cn|in|br|mx|ar|za|ae|sa|kw|qa|om|bh|jo|lb|eg|ma|tn|dz|ly|sd|ye|iq|sy|ps|af|pk|bd|lk|mm|kh|la|vn|th|my|sg|id|ph|nz|ie|is|lu|mt|cy|gr|pt|ro|bg|hr|si|sk|hu|ee|lv|lt|by|ua|md|ge|am|az|kz|uz|tm|kg|tj|mn|np|bt|mv|tw|hk|mo|kr|jp|cn|ru|tr|il|ir)\S*',  # domain extensions
    ]
    
    for pattern in link_patterns:
        if re.search(pattern, text_lower):
            return True
    
    return False


def determine_comment_approval(user, comment_body):
    """
    Determine if a comment should be auto-approved based on trust and link detection.
    
    Args:
        user: User instance (comment author)
        comment_body: Comment text content
        
    Returns:
        tuple: (approved: bool, moderation_reason: str or None)
    """
    # Step 1: Check for links (strict rule - always requires moderation)
    if contains_link(comment_body):
        return False, 'contains_link'
    
    # Step 2: Check if user is trusted
    if not is_trusted_commenter(user):
        return False, 'new_user'
    
    # Step 3: Trusted user, no link - auto-approve
    return True, None
