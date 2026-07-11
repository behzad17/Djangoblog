"""
Highly specific category fallback terms for Related Experts.

Used only when a discussion or post has no extractable keywords. Broad
categories (law, daily life, work, etc.) intentionally have no fallback.
"""

COMMUNITY_SPECIFIC_CATEGORY_FALLBACK: dict[str, list[str]] = {
    'immigration-residency': ['مهاجرت', 'اقامت', 'ویزا'],
    'health': ['پزشک', 'درمان', 'medical'],
}

BLOG_SPECIFIC_CATEGORY_FALLBACK: dict[str, list[str]] = {
    'law-integration': ['مهاجرت', 'اقامت', 'ویزا'],
    'careers-economy': ['حسابداری', 'مالی', 'مالیاتی'],
}
