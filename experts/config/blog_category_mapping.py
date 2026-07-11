"""
Map blog post categories to related expert specialty terms.

Add or update entries here when new blog categories are introduced.
Matching logic in ``experts.selectors.related`` reads from this module only.
"""

BLOG_TO_EXPERT_SPECIALTIES: dict[str, list[str]] = {
    'platform-updates': [],
    'careers-economy': ['کار', 'تحصیل', 'شغل', 'آموزش', 'استخدام', 'مالی', 'حسابداری'],
    'life-in-sweden': ['زندگی', 'اجتماعی'],
    'law-integration': ['مهاجرت', 'اقامت', 'ویزا', 'قانون'],
    'skills-learning': ['کار', 'تحصیل', 'شغل', 'آموزش', 'استخدام'],
    'events-announcements': ['فرهنگ', 'رویداد', 'سرگرمی'],
    'photo-gallery': ['فرهنگ', 'سرگرمی'],
    'public-services': ['خدمات', 'سلامت'],
    'stories-experiences': ['فرهنگ', 'زندگی'],
    'community-engagement': ['زندگی', 'اجتماعی', 'جامعه'],
}
