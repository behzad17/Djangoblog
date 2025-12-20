# Page View Tracking Implementation Guide

## 1. Implementation Options Overview

### Option A: Server-Side Tracking (Recommended for Django) ⭐⭐⭐⭐⭐
**Pros:**
- Full control over data
- Works even with JavaScript disabled
- Better privacy control
- No external dependencies
- GDPR compliance easier

**Cons:**
- Requires database storage
- Slightly more server load
- Need to handle bot filtering

### Option B: Client-Side Tracking (JavaScript)
**Pros:**
- Can track user interactions (scroll, time on page)
- Less server load
- Real-time analytics

**Cons:**
- Requires JavaScript enabled
- Can be blocked by ad blockers
- Privacy concerns (cookies)
- GDPR compliance more complex

### Option C: External Analytics (Google Analytics, Matomo)
**Pros:**
- No development needed
- Advanced analytics features
- Professional dashboards

**Cons:**
- Privacy concerns (GDPR)
- External dependency
- Data stored externally
- Cookie consent required

**Recommendation:** Use **Server-Side Tracking** for accurate, privacy-compliant tracking.

---

## 2. Server-Side Implementation (Django)

### 2.1 Data Model Design

```python
# blog/models.py

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import hashlib

class PageView(models.Model):
    """
    Tracks individual page views with deduplication support.
    """
    # What was viewed
    post = models.ForeignKey(
        'Post',
        on_delete=models.CASCADE,
        related_name='page_views',
        null=True,
        blank=True
    )
    url_path = models.CharField(
        max_length=500,
        help_text="Full URL path for non-post pages"
    )
    
    # Who viewed (optional for privacy)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='page_views'
    )
    
    # Session tracking (for deduplication)
    session_key = models.CharField(
        max_length=40,
        db_index=True,
        help_text="Django session key for session-based deduplication"
    )
    
    # Anonymized tracking
    ip_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA256 hash of IP address (anonymized for privacy)"
    )
    user_agent_hash = models.CharField(
        max_length=64,
        db_index=True,
        help_text="SHA256 hash of user agent (anonymized)"
    )
    
    # When viewed
    viewed_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    # Additional metadata
    referer = models.CharField(
        max_length=500,
        blank=True,
        help_text="HTTP Referer header"
    )
    is_bot = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Whether this view is from a bot/crawler"
    )
    
    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['post', '-viewed_at']),
            models.Index(fields=['session_key', 'post']),
            models.Index(fields=['ip_hash', 'user_agent_hash', 'post']),
        ]
    
    def __str__(self):
        if self.post:
            return f"View of {self.post.title} at {self.viewed_at}"
        return f"View of {self.url_path} at {self.viewed_at}"


class PostViewCount(models.Model):
    """
    Aggregated view count cache for performance.
    Updated periodically or via signals.
    """
    post = models.OneToOneField(
        'Post',
        on_delete=models.CASCADE,
        related_name='view_count_cache'
    )
    total_views = models.PositiveIntegerField(default=0)
    unique_views = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Post View Count"
        verbose_name_plural = "Post View Counts"
    
    def __str__(self):
        return f"{self.post.title}: {self.total_views} views"
```

### 2.2 Helper Functions for Privacy & Deduplication

```python
# blog/utils.py

import hashlib
import re
from django.utils import timezone
from datetime import timedelta

def anonymize_ip(ip_address):
    """
    Hash IP address for privacy (SHA256).
    Returns first 16 characters for indexing efficiency.
    """
    if not ip_address:
        return None
    return hashlib.sha256(ip_address.encode()).hexdigest()[:16]

def anonymize_user_agent(user_agent):
    """
    Hash user agent for privacy.
    """
    if not user_agent:
        return None
    return hashlib.sha256(user_agent.encode()).hexdigest()[:16]

def is_bot_request(user_agent, ip_address):
    """
    Detect common bots and crawlers.
    Returns True if request appears to be from a bot.
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
    ]
    
    user_agent_lower = user_agent.lower()
    for pattern in bot_patterns:
        if re.search(pattern, user_agent_lower):
            return True
    
    return False

def get_client_ip(request):
    """
    Get client IP address from request, handling proxies.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip
```

### 2.3 Middleware Implementation (Recommended Approach)

```python
# blog/middleware.py

from django.utils.deprecation import MiddlewareMixin
from django.db import transaction
from .models import PageView, PostViewCount
from .utils import (
    anonymize_ip, anonymize_user_agent, is_bot_request, get_client_ip
)
from django.contrib.sessions.models import Session
import logging

logger = logging.getLogger(__name__)

class PageViewTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track page views automatically.
    Only tracks GET requests to avoid counting form submissions.
    """
    
    # URLs to exclude from tracking
    EXCLUDED_PATHS = [
        '/admin/',
        '/static/',
        '/media/',
        '/favicon.ico',
        '/robots.txt',
    ]
    
    # Rate limiting: max views per session per post per hour
    RATE_LIMIT_HOURS = 1
    
    def process_response(self, request, response):
        """
        Track page view after response is generated.
        Only track successful GET requests.
        """
        # Only track GET requests with 200 status
        if request.method != 'GET' or response.status_code != 200:
            return response
        
        # Skip excluded paths
        if any(request.path.startswith(path) for path in self.EXCLUDED_PATHS):
            return response
        
        # Skip AJAX requests (optional - you may want to track these)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return response
        
        # Track in background to avoid blocking response
        try:
            self._track_page_view(request)
        except Exception as e:
            # Log error but don't break the request
            logger.error(f"Error tracking page view: {e}", exc_info=True)
        
        return response
    
    def _track_page_view(self, request):
        """
        Track a page view with deduplication.
        """
        # Get request metadata
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        referer = request.META.get('HTTP_REFERER', '')
        session_key = request.session.session_key
        
        # Skip if bot
        if is_bot_request(user_agent, ip_address):
            return
        
        # Anonymize for privacy
        ip_hash = anonymize_ip(ip_address)
        user_agent_hash = anonymize_user_agent(user_agent)
        
        # Try to identify the post from URL
        post = self._get_post_from_request(request)
        
        # Check rate limiting (prevent duplicate counting)
        if self._is_duplicate_view(request, post, session_key, ip_hash, user_agent_hash):
            return
        
        # Create page view record
        with transaction.atomic():
            PageView.objects.create(
                post=post,
                url_path=request.path,
                user=request.user if request.user.is_authenticated else None,
                session_key=session_key or '',
                ip_hash=ip_hash,
                user_agent_hash=user_agent_hash,
                referer=referer,
                is_bot=False,
            )
            
            # Update aggregated count (async or via signal for better performance)
            if post:
                self._update_view_count(post)
    
    def _get_post_from_request(self, request):
        """
        Extract Post object from request URL.
        Assumes URL pattern like: /blog/post-slug/
        """
        from .models import Post
        
        # Try to match post slug from URL
        # Adjust pattern based on your URL structure
        path_parts = request.path.strip('/').split('/')
        
        if len(path_parts) >= 2 and path_parts[0] in ['blog', 'post']:
            slug = path_parts[-1]
            try:
                return Post.objects.get(slug=slug, status=1)  # Only published posts
            except Post.DoesNotExist:
                pass
        
        return None
    
    def _is_duplicate_view(self, request, post, session_key, ip_hash, user_agent_hash):
        """
        Check if this view should be considered a duplicate.
        Uses multiple strategies:
        1. Same session + same post within rate limit window
        2. Same IP + user agent + post within rate limit window
        """
        from django.utils import timezone
        from datetime import timedelta
        
        if not post:
            return False
        
        cutoff_time = timezone.now() - timedelta(hours=self.RATE_LIMIT_HOURS)
        
        # Check session-based deduplication
        if session_key:
            recent_view = PageView.objects.filter(
                post=post,
                session_key=session_key,
                viewed_at__gte=cutoff_time
            ).exists()
            if recent_view:
                return True
        
        # Check IP + User Agent deduplication (for users without sessions)
        if ip_hash and user_agent_hash:
            recent_view = PageView.objects.filter(
                post=post,
                ip_hash=ip_hash,
                user_agent_hash=user_agent_hash,
                viewed_at__gte=cutoff_time
            ).exists()
            if recent_view:
                return True
        
        return False
    
    def _update_view_count(self, post):
        """
        Update aggregated view count cache.
        For better performance, consider doing this asynchronously.
        """
        view_count, created = PostViewCount.objects.get_or_create(post=post)
        view_count.total_views = PageView.objects.filter(
            post=post, is_bot=False
        ).count()
        view_count.unique_views = PageView.objects.filter(
            post=post, is_bot=False
        ).values('session_key', 'ip_hash', 'user_agent_hash').distinct().count()
        view_count.save()
```

### 2.4 Alternative: View-Based Tracking (Simpler)

If middleware seems complex, you can track directly in views:

```python
# blog/views.py (add to post_detail function)

from .models import PageView, PostViewCount
from .utils import (
    anonymize_ip, anonymize_user_agent, is_bot_request, get_client_ip
)
from django.utils import timezone
from datetime import timedelta

@ratelimit(key='ip', rate='5/m', method='POST', block=True)
def post_detail(request, slug):
    # ... existing code ...
    
    queryset = Post.objects.filter(status=1).select_related('category', 'author')
    post = get_object_or_404(queryset, slug=slug)
    
    # Track page view (only for GET requests)
    if request.method == 'GET':
        track_page_view(request, post)
    
    # ... rest of existing code ...
```

```python
# blog/utils.py (add this function)

def track_page_view(request, post):
    """
    Track a page view for a post with deduplication.
    """
    # Skip bots
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    
    if is_bot_request(user_agent, ip_address):
        return
    
    # Anonymize
    ip_hash = anonymize_ip(ip_address)
    user_agent_hash = anonymize_user_agent(user_agent)
    session_key = request.session.session_key or ''
    
    # Rate limiting: check for recent view
    cutoff_time = timezone.now() - timedelta(hours=1)
    
    # Check session-based duplicate
    if session_key:
        if PageView.objects.filter(
            post=post,
            session_key=session_key,
            viewed_at__gte=cutoff_time
        ).exists():
            return
    
    # Check IP+UA-based duplicate
    if ip_hash and user_agent_hash:
        if PageView.objects.filter(
            post=post,
            ip_hash=ip_hash,
            user_agent_hash=user_agent_hash,
            viewed_at__gte=cutoff_time
        ).exists():
            return
    
    # Create view record
    PageView.objects.create(
        post=post,
        url_path=request.path,
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key,
        ip_hash=ip_hash,
        user_agent_hash=ip_hash,
        referer=request.META.get('HTTP_REFERER', ''),
        is_bot=False,
    )
    
    # Update cache (consider doing this asynchronously)
    view_count, _ = PostViewCount.objects.get_or_create(post=post)
    view_count.total_views = PageView.objects.filter(
        post=post, is_bot=False
    ).count()
    view_count.save()
```

### 2.5 Add View Count to Post Model

```python
# blog/models.py (add to Post model)

class Post(models.Model):
    # ... existing fields ...
    
    def view_count(self):
        """
        Get total view count for this post.
        Uses cached count for performance.
        """
        if hasattr(self, 'view_count_cache'):
            return self.view_count_cache.total_views
        return PageView.objects.filter(post=self, is_bot=False).count()
    
    def unique_view_count(self):
        """
        Get unique view count (approximate).
        """
        if hasattr(self, 'view_count_cache'):
            return self.view_count_cache.unique_views
        return PageView.objects.filter(
            post=self, is_bot=False
        ).values('session_key', 'ip_hash', 'user_agent_hash').distinct().count()
```

---

## 3. Deduplication Strategies

### 3.1 Session-Based Deduplication
- **How:** Track views per Django session key
- **Pros:** Accurate for logged-in users
- **Cons:** Doesn't work for users without sessions

### 3.2 IP + User Agent Hash
- **How:** Combine anonymized IP + user agent hash
- **Pros:** Works for all users
- **Cons:** Less accurate (shared IPs, VPNs)

### 3.3 Time-Based Rate Limiting
- **How:** Only count one view per post per session/IP per hour
- **Pros:** Prevents refresh spam
- **Cons:** Legitimate multiple views from same user won't count

### 3.4 Recommended Combination
Use **all three**:
1. Primary: Session key + post + time window
2. Fallback: IP hash + user agent hash + post + time window
3. Time window: 1 hour (adjustable)

---

## 4. Privacy & GDPR Considerations

### 4.1 Data Minimization
✅ **Do:**
- Hash IP addresses (SHA256)
- Hash user agents
- Store minimal data
- Set data retention period

❌ **Don't:**
- Store full IP addresses
- Store full user agents
- Store personal data unnecessarily

### 4.2 Cookie Consent
- **Session cookies:** Usually exempt (essential for functionality)
- **Tracking cookies:** Require consent
- **Recommendation:** Use session-based tracking (no additional cookies needed)

### 4.3 Data Retention
```python
# blog/management/commands/cleanup_old_views.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from blog.models import PageView

class Command(BaseCommand):
    help = 'Delete page views older than retention period'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=365,
            help='Retention period in days (default: 365)'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        cutoff_date = timezone.now() - timedelta(days=days)
        
        deleted = PageView.objects.filter(viewed_at__lt=cutoff_date).delete()
        self.stdout.write(
            self.style.SUCCESS(f'Deleted {deleted[0]} old page views')
        )
```

### 4.4 User Rights (GDPR)
- **Right to access:** Provide view count data if requested
- **Right to deletion:** Allow users to request data deletion
- **Privacy policy:** Document what data is collected

---

## 5. Database Migrations

```bash
# Create migrations
python manage.py makemigrations blog

# Apply migrations
python manage.py migrate blog
```

---

## 6. Settings Configuration

```python
# codestar/settings.py or sweden_today/settings.py

# Add middleware (if using middleware approach)
MIDDLEWARE = [
    # ... existing middleware ...
    'blog.middleware.PageViewTrackingMiddleware',
    # ... rest of middleware ...
]

# Optional: Configure logging
LOGGING = {
    'version': 1,
    'handlers': {
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'page_views.log',
        },
    },
    'loggers': {
        'blog.middleware': {
            'handlers': ['file'],
            'level': 'ERROR',
        },
    },
}
```

---

## 7. Display View Counts in Templates

```django
{# blog/templates/blog/post_detail.html #}

<div class="post-meta">
    <span class="view-count">
        <i class="fas fa-eye"></i>
        {{ post.view_count }} views
    </span>
    <span class="comment-count">
        <i class="far fa-comments"></i>
        {{ comment_count }} comments
    </span>
</div>
```

---

## 8. Admin Interface

```python
# blog/admin.py

from django.contrib import admin
from .models import PageView, PostViewCount

@admin.register(PageView)
class PageViewAdmin(admin.ModelAdmin):
    list_display = ['post', 'user', 'viewed_at', 'ip_hash', 'is_bot']
    list_filter = ['is_bot', 'viewed_at']
    search_fields = ['post__title', 'url_path']
    readonly_fields = ['viewed_at']
    date_hierarchy = 'viewed_at'

@admin.register(PostViewCount)
class PostViewCountAdmin(admin.ModelAdmin):
    list_display = ['post', 'total_views', 'unique_views', 'last_updated']
    search_fields = ['post__title']
    readonly_fields = ['last_updated']
```

---

## 9. Performance Optimization

### 9.1 Use Database Indexes
Already included in model definition above.

### 9.2 Async Updates
For high-traffic sites, update `PostViewCount` asynchronously:

```python
# Use Celery or Django-Q for async tasks
from celery import shared_task

@shared_task
def update_post_view_count(post_id):
    post = Post.objects.get(pk=post_id)
    view_count, _ = PostViewCount.objects.get_or_create(post=post)
    view_count.total_views = PageView.objects.filter(
        post=post, is_bot=False
    ).count()
    view_count.save()
```

### 9.3 Caching
```python
from django.core.cache import cache

def get_view_count(post):
    cache_key = f'post_view_count_{post.id}'
    count = cache.get(cache_key)
    if count is None:
        count = post.view_count()
        cache.set(cache_key, count, 300)  # Cache for 5 minutes
    return count
```

---

## 10. Testing

```python
# blog/tests.py

from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import Post, PageView

class PageViewTrackingTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@test.com', 'password')
        self.post = Post.objects.create(
            title='Test Post',
            slug='test-post',
            author=self.user,
            content='Test content',
            status=1
        )
        self.client = Client()
    
    def test_tracks_page_view(self):
        response = self.client.get(f'/blog/{self.post.slug}/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(PageView.objects.filter(post=self.post).count(), 1)
    
    def test_deduplication_prevents_duplicate_views(self):
        # First view
        self.client.get(f'/blog/{self.post.slug}/')
        # Second view within rate limit
        self.client.get(f'/blog/{self.post.slug}/')
        # Should only count as 1 view
        self.assertEqual(PageView.objects.filter(post=self.post).count(), 1)
    
    def test_bot_filtering(self):
        # Simulate bot request
        response = self.client.get(
            f'/blog/{self.post.slug}/',
            HTTP_USER_AGENT='Googlebot/2.1'
        )
        self.assertEqual(response.status_code, 200)
        # Should not create page view
        self.assertEqual(PageView.objects.filter(post=self.post).count(), 0)
```

---

## 11. Recommended Implementation Steps

1. **Create models** (`PageView`, `PostViewCount`)
2. **Create migrations** and apply them
3. **Add utility functions** (`utils.py`)
4. **Choose approach:**
   - **Middleware** (automatic, all pages)
   - **View-based** (manual, specific pages)
5. **Add tracking code** to views or middleware
6. **Update Post model** with `view_count()` method
7. **Display in templates**
8. **Set up admin interface**
9. **Configure cleanup job** (cron/celery)
10. **Test thoroughly**

---

## 12. Summary

**Best Approach for Django:**
- ✅ Server-side tracking with middleware
- ✅ Session + IP+UA deduplication
- ✅ Anonymized data (hashed IP/UA)
- ✅ Bot filtering
- ✅ Rate limiting (1 hour window)
- ✅ Aggregated counts for performance
- ✅ GDPR compliant (minimal data, anonymized)

**Privacy-First Design:**
- No cookies required (uses Django sessions)
- IP addresses hashed (SHA256)
- User agents hashed
- Configurable retention period
- No personal data stored unnecessarily

This implementation provides accurate, privacy-compliant page view tracking suitable for GDPR-regulated environments.

