"""Seed UsefulLinkCategory rows and assign RelatedLink.category from link_type."""

from django.db import migrations


CATEGORY_SEED = [
    {
        'name_en': 'Government & Public Services',
        'name_fa': 'دولت و خدمات عمومی',
        'slug': 'government',
        'icon': 'bi-building',
        'display_order': 1,
    },
    {
        'name_en': 'Migration & Integration',
        'name_fa': 'مهاجرت و ادغام',
        'slug': 'migration',
        'icon': 'bi-compass',
        'display_order': 2,
    },
    {
        'name_en': 'Politics & Political Parties',
        'name_fa': 'سیاست و احزاب سیاسی',
        'slug': 'politics',
        'icon': 'bi-flag',
        'display_order': 3,
    },
    {
        'name_en': 'News & Media',
        'name_fa': 'اخبار و رسانه',
        'slug': 'news-media',
        'icon': 'bi-newspaper',
        'display_order': 4,
    },
    {
        'name_en': 'Universities',
        'name_fa': 'دانشگاه‌ها',
        'slug': 'universities',
        'icon': 'bi-mortarboard',
        'display_order': 5,
    },
    {
        'name_en': 'Swedish Language',
        'name_fa': 'زبان سوئدی',
        'slug': 'swedish-language',
        'icon': 'bi-translate',
        'display_order': 6,
    },
    {
        'name_en': 'Adult Education',
        'name_fa': 'آموزش بزرگسالان',
        'slug': 'adult-education',
        'icon': 'bi-book',
        'display_order': 7,
    },
    {
        'name_en': 'Podcasts',
        'name_fa': 'پادکست‌ها',
        'slug': 'podcasts',
        'icon': 'bi-mic',
        'display_order': 8,
    },
    {
        'name_en': 'Movies & Videos',
        'name_fa': 'فیلم و ویدئو',
        'slug': 'movies-videos',
        'icon': 'bi-camera-video',
        'display_order': 9,
    },
    {
        'name_en': 'Radio',
        'name_fa': 'رادیو',
        'slug': 'radio',
        'icon': 'bi-broadcast',
        'display_order': 10,
    },
    {
        'name_en': 'Social Media',
        'name_fa': 'شبکه‌های اجتماعی',
        'slug': 'social-media',
        'icon': 'bi-share',
        'display_order': 11,
    },
    {
        'name_en': 'Public Figures',
        'name_fa': 'چهره‌های عمومی',
        'slug': 'public-figures',
        'icon': 'bi-person-badge',
        'display_order': 12,
    },
    {
        'name_en': 'Iranian Community',
        'name_fa': 'جامعه ایرانی',
        'slug': 'iranian-community',
        'icon': 'bi-people',
        'display_order': 13,
    },
    {
        'name_en': 'Essential Apps',
        'name_fa': 'اپلیکیشن‌های ضروری',
        'slug': 'essential-apps',
        'icon': 'bi-phone',
        'display_order': 14,
    },
    {
        'name_en': 'Buy & Sell',
        'name_fa': 'خرید و فروش',
        'slug': 'buy-sell',
        'icon': 'bi-cart',
        'display_order': 15,
    },
    {
        'name_en': 'Banks & Financial Services',
        'name_fa': 'بانک و خدمات مالی',
        'slug': 'banks',
        'icon': 'bi-bank',
        'display_order': 16,
    },
    {
        'name_en': 'Insurance',
        'name_fa': 'بیمه',
        'slug': 'insurance',
        'icon': 'bi-shield-check',
        'display_order': 17,
    },
    {
        'name_en': 'Healthcare',
        'name_fa': 'سلامت و درمان',
        'slug': 'healthcare',
        'icon': 'bi-heart-pulse',
        'display_order': 18,
    },
]

LINK_TYPE_TO_CATEGORY_SLUG = {
    'podcast': 'podcasts',
    'video': 'movies-videos',
    'radio': 'radio',
    'social': 'social-media',
    'website': 'essential-apps',
    'file': 'adult-education',
}


def seed_categories_and_assign_links(apps, schema_editor):
    UsefulLinkCategory = apps.get_model('related_links', 'UsefulLinkCategory')
    RelatedLink = apps.get_model('related_links', 'RelatedLink')

    slug_to_category = {}
    for row in CATEGORY_SEED:
        category, _ = UsefulLinkCategory.objects.update_or_create(
            slug=row['slug'],
            defaults={
                'name_en': row['name_en'],
                'name_fa': row['name_fa'],
                'icon': row['icon'],
                'display_order': row['display_order'],
                'is_active': True,
            },
        )
        slug_to_category[row['slug']] = category

    fallback = slug_to_category.get('essential-apps')
    for link in RelatedLink.objects.all():
        category_slug = LINK_TYPE_TO_CATEGORY_SLUG.get(link.link_type, 'essential-apps')
        category = slug_to_category.get(category_slug, fallback)
        if category:
            link.category_id = category.id
            link.save(update_fields=['category_id'])


class Migration(migrations.Migration):

    dependencies = [
        ('related_links', '0002_usefullinkcategory_relatedlink_category'),
    ]

    operations = [
        migrations.RunPython(seed_categories_and_assign_links, migrations.RunPython.noop),
    ]
