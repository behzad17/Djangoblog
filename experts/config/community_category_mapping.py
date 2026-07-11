"""
Map community discussion categories to related expert specialty terms.

Add or update entries here when new community categories are introduced.
Matching logic in ``experts.selectors.related`` reads from this module only.
"""

COMMUNITY_TO_EXPERT_SPECIALTIES: dict[str, list[str]] = {
    'immigration-residency': ['مهاجرت', 'اقامت', 'ویزا'],
    'work-education': ['کار', 'تحصیل', 'شغل', 'آموزش', 'استخدام'],
    'daily-life': ['زندگی', 'اجتماعی'],
    'law-legal': ['حقوق', 'وکیل', 'قانون', 'legal'],
    'health': ['پزشک', 'سلامت', 'درمان', 'health', 'medical'],
    'culture-events': ['فرهنگ', 'رویداد', 'سرگرمی'],
    'buy-sell': ['خرید', 'فروش', 'کسب'],
    'general': [],
}


def expert_specialties_for_community_category(community_slug: str) -> list[str]:
    """Return specialty search terms related to a community category slug."""
    return list(COMMUNITY_TO_EXPERT_SPECIALTIES.get(community_slug, []))
