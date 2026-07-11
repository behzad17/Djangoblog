"""
Map community discussion categories to related useful link category slugs.

Add or update entries here when new community categories are introduced.
Matching logic in ``related_links.selectors.related`` reads from this module only.
"""

COMMUNITY_TO_USEFUL_LINK_CATEGORY_SLUGS: dict[str, list[str]] = {
    'immigration-residency': ['migration', 'government', 'iranian-community'],
    'work-education': ['universities', 'swedish-language', 'adult-education'],
    'daily-life': ['essential-apps', 'banks', 'social-media'],
    'law-legal': ['government', 'politics'],
    'health': ['healthcare', 'insurance'],
    'culture-events': [
        'news-media',
        'podcasts',
        'movies-videos',
        'radio',
        'public-figures',
        'iranian-community',
    ],
    'buy-sell': ['buy-sell'],
    'general': [],
}


def useful_link_category_slugs_for_community_category(
    community_slug: str,
) -> list[str]:
    """Return useful link category slugs related to a community category slug."""
    return list(COMMUNITY_TO_USEFUL_LINK_CATEGORY_SLUGS.get(community_slug, []))
