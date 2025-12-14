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
