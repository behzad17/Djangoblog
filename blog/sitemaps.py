from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Post, Category


class PostSitemap(Sitemap):
    """Sitemap for published blog posts."""
    changefreq = "weekly"
    priority = 0.9

    def items(self):
        """Return all published posts."""
        return Post.objects.filter(status=1)

    def lastmod(self, obj):
        """Return the last modification date of the post."""
        return obj.updated_on

    def location(self, obj):
        """Return the URL of the post."""
        return reverse('post_detail', args=[obj.slug])


class CategorySitemap(Sitemap):
    """Sitemap for blog categories."""
    changefreq = "daily"
    priority = 0.7

    def items(self):
        """Return all categories."""
        return Category.objects.all()

    def lastmod(self, obj):
        """Return the creation date of the category."""
        return obj.created_on

    def location(self, obj):
        """Return the URL of the category."""
        return reverse('category_posts', args=[obj.slug])

