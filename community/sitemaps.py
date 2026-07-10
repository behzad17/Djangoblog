from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from community.selectors.discussions import list_discussions


class DiscussionSitemap(Sitemap):
    """Sitemap for public community discussions."""

    changefreq = 'weekly'
    priority = 0.8

    def items(self):
        return list_discussions()

    def lastmod(self, obj):
        return obj.last_activity_at

    def location(self, obj):
        return reverse('community:discussion_detail', args=[obj.slug])
