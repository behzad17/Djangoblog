from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from django.utils.text import slugify
from django.utils import timezone


class AdCategory(models.Model):
    """
    Category for grouping advertisements.

    There will typically be around 10 categories, each with its own listing page.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Advertisement Category"
        verbose_name_plural = "Advertisement Categories"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def ad_count(self):
        """Return number of approved, active ads in this category."""
        return self.ads.filter(is_active=True, is_approved=True).count()


class Ad(models.Model):
    """
    An advertisement with image and click-through URL.

    - Each Ad belongs to a category.
    - Each Ad has its own detail page (slug-based URL).
    - Image is displayed at 250x500 via CSS on the site.
    - The image links to a custom URL provided by the advertiser.
    - Visibility is controlled via approval and active flags and optional date range.
    """

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    category = models.ForeignKey(
        AdCategory,
        on_delete=models.PROTECT,
        related_name="ads",
    )
    owner = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ads",
        null=True,
        blank=True,
        help_text="User who created this ad",
    )

    image = CloudinaryField(
        "ad_image",
        blank=False,
        help_text="Upload the main ad image (will be displayed at 250x500).",
    )

    target_url = models.URLField(
        max_length=500,
        help_text="External URL to open when the ad is clicked.",
    )
    url_approved = models.BooleanField(
        default=False,
        help_text="Whether the target URL has been reviewed and approved by an admin.",
    )
    city = models.CharField(
        max_length=100,
        blank=True,
        help_text="City where the service/business is located (optional).",
    )

    # Moderation and scheduling
    is_active = models.BooleanField(
        default=True,
        help_text="Uncheck to hide this ad without deleting it.",
    )
    is_approved = models.BooleanField(
        default=False,
        help_text="Only approved ads will be visible on the site.",
    )
    start_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional start date for showing this ad.",
    )
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Optional end date for showing this ad.",
    )

    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)

    # Featured ad feature
    is_featured = models.BooleanField(
        default=False,
        help_text="Featured ads appear first in listings and have special highlighting.",
    )
    featured_priority = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        help_text="Priority for featured ads (1-39). Lower numbers appear first. Ads with priority 1-39 appear in top positions on page 1. Leave blank for automatic ordering by date.",
    )
    featured_until = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional: Featured status expires after this date. Leave blank for permanent featured status.",
    )

    class Meta:
        ordering = ["-created_on"]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        """
        Automatically generate a unique slug from the title if not set.
        """
        if not self.slug:
            base_slug = slugify(self.title)
            slug = base_slug
            counter = 1
            while Ad.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def is_currently_visible(self):
        """
        Check if the ad should be shown based on approval, active flag, and date range.
        """
        if not (self.is_active and self.is_approved and self.url_approved):
            return False

        today = timezone.now().date()
        if self.start_date and today < self.start_date:
            return False
        if self.end_date and today > self.end_date:
            return False
        return True

    def is_currently_featured(self):
        """
        Check if the ad is currently featured (is_featured=True and featured_until is in future or null).
        """
        if not self.is_featured:
            return False
        if self.featured_until is None:
            return True
        return timezone.now() < self.featured_until


class FavoriteAd(models.Model):
    """
    A model representing a user's favorite/saved advertisement.
    
    This model creates a many-to-many relationship between users and ads,
    allowing users to save ads for later reference. It includes a timestamp
    of when the ad was favorited.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ad = models.ForeignKey(Ad, on_delete=models.CASCADE, related_name='favorites')
    added_on = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Meta options for FavoriteAd model."""
        unique_together = ('user', 'ad')

    def __str__(self):
        """Returns a string representation of the favorite."""
        return f"{self.user.username} saved {self.ad.title}"


class AdComment(models.Model):
    """
    A model representing a comment on an advertisement.
    
    Ad comments are published immediately (no moderation queue).
    Comments can be soft-deleted via is_deleted flag.
    """
    ad = models.ForeignKey(
        Ad,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="The advertisement this comment belongs to"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ad_comments",
        help_text="User who wrote this comment"
    )
    body = models.TextField(
        help_text="Comment text content"
    )
    created_on = models.DateTimeField(
        auto_now_add=True,
        help_text="When this comment was created"
    )
    updated_on = models.DateTimeField(
        auto_now=True,
        help_text="When this comment was last updated"
    )
    is_deleted = models.BooleanField(
        default=False,
        help_text="Soft delete flag (hide comment without deleting)"
    )

    class Meta:
        """Meta options for AdComment model."""
        ordering = ["created_on"]
        indexes = [
            models.Index(fields=['ad', 'created_on']),
            models.Index(fields=['author', 'created_on']),
        ]
        verbose_name = "Ad Comment"
        verbose_name_plural = "Ad Comments"

    def __str__(self):
        """Returns a string representation of the comment."""
        return f"Comment on {self.ad.title} by {self.author.username}"


# Create your models here.
