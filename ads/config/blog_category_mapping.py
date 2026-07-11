"""
Map blog post categories to related ad category slugs.

Add or update entries here when new blog categories are introduced.
Matching logic in ``ads.selectors.related`` reads from this module only.
"""

BLOG_TO_AD_CATEGORY_SLUGS: dict[str, list[str]] = {
    'platform-updates': [],
    'careers-economy': ['work-services', 'mozsh-zbn-o-dr'],
    'life-in-sweden': ['social-zendegi', 'food-restaurant', 'leisure'],
    'law-integration': ['legal-financial', 'social-zendegi'],
    'skills-learning': ['work-services', 'mozsh-zbn-o-dr'],
    'events-announcements': ['leisure', 'food-restaurant'],
    'photo-gallery': ['leisure'],
    'public-services': ['legal-financial', 'health-welfare'],
    'stories-experiences': ['social-zendegi', 'leisure'],
    'community-engagement': ['social-zendegi'],
}
