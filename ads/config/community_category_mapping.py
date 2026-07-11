"""
Map community discussion categories to related ad category slugs.

Add or update entries here when new community categories are introduced.
Matching logic in ``ads.selectors.related`` reads from this module only.
"""

COMMUNITY_TO_AD_CATEGORY_SLUGS: dict[str, list[str]] = {
    'immigration-residency': ['legal-financial', 'social-zendegi'],
    'work-education': ['work-services', 'mozsh-zbn-o-dr'],
    'daily-life': ['social-zendegi', 'food-restaurant', 'leisure'],
    'law-legal': ['legal-financial'],
    'health': ['health-welfare', 'beauty-appliances'],
    'culture-events': ['leisure', 'food-restaurant'],
    'buy-sell': [],
    'general': [],
}


def ad_category_slugs_for_community_category(community_slug: str) -> list[str]:
    """Return ad category slugs related to a community category slug."""
    return list(COMMUNITY_TO_AD_CATEGORY_SLUGS.get(community_slug, []))
