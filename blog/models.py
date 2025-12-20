from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.utils import timezone


# Create your models here.
STATUS = ((0, "Draft"), (1, "Published"))


class UserProfile(models.Model):
    """
    Extended user profile with expert publishing permissions.
    
    This model extends the Django User model to add expert access control.
    Expert users can publish posts without admin approval.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile',
        help_text="The user account associated with this profile"
    )
    can_publish_without_approval = models.BooleanField(
        default=False,
        help_text="If True, user's posts will be published automatically without admin approval."
    )
    expert_since = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When expert access was granted"
    )
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-expert_since']
    
    def __str__(self):
        expert_status = "Expert" if self.can_publish_without_approval else "Regular"
        return f"{self.user.username} - {expert_status}"
    
    def save(self, *args, **kwargs):
        """Set expert_since when access is granted for the first time."""
        if self.can_publish_without_approval and not self.expert_since:
            self.expert_since = timezone.now()
        elif not self.can_publish_without_approval:
            self.expert_since = None
        super().save(*args, **kwargs)


class Category(models.Model):
    """
    A model representing a blog post category.
    
    Categories help organize posts and allow users to filter content
    by topic or theme.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """Meta options for Category model."""
        verbose_name_plural = "Categories"
        ordering = ['name']
    
    def __str__(self):
        """Returns a string representation of the category."""
        return self.name
    
    def get_absolute_url(self):
        """Returns the URL for filtering posts by this category."""
        from django.urls import reverse
        return reverse('category_posts', kwargs={'category_slug': self.slug})
    
    def post_count(self):
        """Returns the number of published posts in this category."""
        return self.posts.filter(status=1).count()


class Post(models.Model):
    """
    A model representing a blog post.
    
    This model stores all the information about a blog post including its title,
    content, author, and publication status. It also handles the featured image
    using Cloudinary for image storage.
    """
    title = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="blog_posts"
    )
    featured_image = CloudinaryField('image', default='placeholder')
    excerpt = models.TextField(blank=True)
    updated_on = models.DateTimeField(auto_now=True)
    content = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    status = models.IntegerField(choices=STATUS, default=0)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='posts'
    )
    external_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        help_text="Optional external URL for this post. Must be approved by admin to be displayed."
    )
    url_approved = models.BooleanField(
        default=False,
        help_text="Whether the external URL has been approved by admin to be displayed."
    )
    pinned = models.BooleanField(
        default=False,
        help_text="Admins can pin a post to appear in the second slot of each row on the homepage."
    )
    pinned_row = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional: Choose the target row (1-based) on the homepage where this post should appear in the second slot. Leave blank to auto-place."
    )
    # Event-specific fields (optional, only for Events category)
    event_start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Start date for Events category posts only"
    )
    event_end_date = models.DateField(
        null=True,
        blank=True,
        help_text="End date for Events category posts only"
    )

    class Meta:
        """Meta options for Post model."""
        ordering = ['-created_on']

    def __str__(self):
        """Returns a string representation of the post."""
        return self.title

    def favorite_count(self):
        """Returns the number of users who have favorited this post."""
        return Favorite.objects.filter(post=self).count()
    
    def like_count(self):
        """Returns the number of users who have liked this post."""
        return Like.objects.filter(post=self).count()
    
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

class Comment(models.Model):
    """
    A model representing a comment on a blog post.
    
    This model stores user comments on blog posts, including the comment text,
    author, and approval status. Comments are linked to both the post and the user
    who created them.
    """
    post = models.ForeignKey(
        Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="commenter")
    body = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=True)

    class Meta:
        """Meta options for Comment model."""
        ordering = ["created_on"]  

    def __str__(self):
        """Returns a string representation of the comment."""
        return f"Comment {self.body} by {self.author}"
           
class Favorite(models.Model):
    """
    A model representing a user's favorite/saved blog post.
    
    This model creates a many-to-many relationship between users and posts,
    allowing users to save posts for later reference. It includes a timestamp
    of when the post was favorited.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)  
    post = models.ForeignKey(Post, on_delete=models.CASCADE)  
    added_on = models.DateTimeField(auto_now_add=True)  

    class Meta:
        """Meta options for Favorite model."""
        unique_together = ('user', 'post') 

    def __str__(self):
        """Returns a string representation of the favorite."""
        return f"{self.user.username} saved {self.post.title}"


class Like(models.Model):
    """
    A model representing a user's like on a blog post.
    
    This model creates a many-to-many relationship between users and posts,
    allowing users to show appreciation for posts with a quick like.
    """
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='likes'
    )
    post = models.ForeignKey(
        Post, 
        on_delete=models.CASCADE,
        related_name='likes'
    )
    created_on = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        """Meta options for Like model."""
        unique_together = ('user', 'post')
        ordering = ['-created_on']
    
    def __str__(self):
        """Returns a string representation of the like."""
        return f"{self.user.username} liked {self.post.title}"


class PageView(models.Model):
    """
    Tracks individual page views with deduplication support.
    
    This model records each page view with anonymized data for privacy compliance.
    Uses hashed IP addresses and user agents to prevent storing personal data.
    """
    # What was viewed
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='page_views',
        null=True,
        blank=True,
        help_text="The post that was viewed (null for non-post pages)"
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
        related_name='page_views',
        help_text="User who viewed (if authenticated)"
    )
    
    # Session tracking (for deduplication)
    session_key = models.CharField(
        max_length=40,
        db_index=True,
        help_text="Django session key for session-based deduplication"
    )
    
    # Anonymized tracking (privacy-compliant)
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
        verbose_name = "Page View"
        verbose_name_plural = "Page Views"
    
    def __str__(self):
        if self.post:
            return f"View of {self.post.title} at {self.viewed_at}"
        return f"View of {self.url_path} at {self.viewed_at}"


class PostViewCount(models.Model):
    """
    Aggregated view count cache for performance.
    
    This model stores pre-calculated view counts to avoid expensive
    queries when displaying view counts. Updated periodically or via signals.
    """
    post = models.OneToOneField(
        Post,
        on_delete=models.CASCADE,
        related_name='view_count_cache'
    )
    total_views = models.PositiveIntegerField(
        default=0,
        help_text="Total number of views (excluding bots)"
    )
    unique_views = models.PositiveIntegerField(
        default=0,
        help_text="Approximate unique views (based on session/IP/UA combination)"
    )
    last_updated = models.DateTimeField(
        auto_now=True,
        help_text="When the count was last updated"
    )
    
    class Meta:
        verbose_name = "Post View Count"
        verbose_name_plural = "Post View Counts"
    
    def __str__(self):
        return f"{self.post.title}: {self.total_views} views"
