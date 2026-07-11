"""
Map blog post categories to related useful link category slugs.

Add or update entries here when new blog categories are introduced.
Matching logic in ``related_links.selectors.related`` reads from this module only.
"""

BLOG_TO_USEFUL_LINK_CATEGORY_SLUGS: dict[str, list[str]] = {
    'platform-updates': ['news-media'],
    'careers-economy': ['universities', 'swedish-language', 'adult-education'],
    'life-in-sweden': ['essential-apps', 'banks', 'social-media'],
    'law-integration': ['migration', 'government', 'iranian-community'],
    'skills-learning': ['universities', 'swedish-language', 'adult-education'],
    'events-announcements': [
        'news-media',
        'podcasts',
        'movies-videos',
        'radio',
    ],
    'photo-gallery': ['movies-videos', 'news-media'],
    'public-services': ['government', 'healthcare', 'insurance'],
    'stories-experiences': ['iranian-community', 'news-media'],
    'community-engagement': ['iranian-community', 'social-media'],
}
