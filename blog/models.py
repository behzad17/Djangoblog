from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField


# Create your models here.
STATUS = ((0, "Draft"), (1, "Published"))


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

    class Meta:
        """Meta options for Post model."""
        ordering = ['-created_on']

    def __str__(self):
        """Returns a string representation of the post."""
        return self.title

    def favorite_count(self):
        """Returns the number of users who have favorited this post."""
        return Favorite.objects.filter(post=self).count()

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
