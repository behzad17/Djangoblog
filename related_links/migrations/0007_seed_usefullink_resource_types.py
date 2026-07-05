"""Seed UsefulLinkResourceType rows and migrate RelatedLink.link_type values."""

from django.db import migrations


RESOURCE_TYPE_SEED = [
    {
        'name_en': 'Website',
        'name_fa': 'وب\u200cسایت',
        'slug': 'website',
        'icon': 'bi-globe',
        'display_order': 1,
        'is_media': False,
    },
    {
        'name_en': 'Application',
        'name_fa': 'اپلیکیشن',
        'slug': 'application',
        'icon': 'bi-phone',
        'display_order': 2,
        'is_media': False,
    },
    {
        'name_en': 'Government Service',
        'name_fa': 'خدمات دولتی',
        'slug': 'government-service',
        'icon': 'bi-building',
        'display_order': 3,
        'is_media': False,
    },
    {
        'name_en': 'Online Service',
        'name_fa': 'سرویس آنلاین',
        'slug': 'online-service',
        'icon': 'bi-cloud',
        'display_order': 4,
        'is_media': False,
    },
    {
        'name_en': 'Document / PDF',
        'name_fa': 'سند / PDF',
        'slug': 'document-pdf',
        'icon': 'bi-file-earmark-text',
        'display_order': 5,
        'is_media': False,
    },
    {
        'name_en': 'Guide / Article',
        'name_fa': 'راهنما / مقاله',
        'slug': 'guide',
        'icon': 'bi-journal-text',
        'display_order': 6,
        'is_media': False,
    },
    {
        'name_en': 'Podcast',
        'name_fa': 'پادکست',
        'slug': 'podcast',
        'icon': 'bi-headphones',
        'display_order': 7,
        'is_media': True,
    },
    {
        'name_en': 'Video',
        'name_fa': 'ویدئو',
        'slug': 'video',
        'icon': 'bi-play-circle',
        'display_order': 8,
        'is_media': True,
    },
    {
        'name_en': 'Radio',
        'name_fa': 'رادیو',
        'slug': 'radio',
        'icon': 'bi-broadcast',
        'display_order': 9,
        'is_media': True,
    },
    {
        'name_en': 'YouTube Channel',
        'name_fa': 'کانال یوتیوب',
        'slug': 'youtube-channel',
        'icon': 'bi-youtube',
        'display_order': 10,
        'is_media': True,
    },
    {
        'name_en': 'Social Media',
        'name_fa': 'شبکه\u200cهای اجتماعی',
        'slug': 'social-media',
        'icon': 'bi-people',
        'display_order': 11,
        'is_media': True,
    },
    {
        'name_en': 'Service Center',
        'name_fa': 'مرکز خدمات',
        'slug': 'service-center',
        'icon': 'bi-geo-alt',
        'display_order': 12,
        'is_media': False,
    },
]

LINK_TYPE_TO_RESOURCE_SLUG = {
    'website': 'website',
    'podcast': 'podcast',
    'video': 'video',
    'radio': 'radio',
    'social': 'social-media',
    'file': 'document-pdf',
}


def seed_resource_types_and_migrate_links(apps, schema_editor):
    UsefulLinkResourceType = apps.get_model('related_links', 'UsefulLinkResourceType')
    RelatedLink = apps.get_model('related_links', 'RelatedLink')

    slug_to_type = {}
    for row in RESOURCE_TYPE_SEED:
        resource_type, _ = UsefulLinkResourceType.objects.update_or_create(
            slug=row['slug'],
            defaults=row,
        )
        slug_to_type[row['slug']] = resource_type

    default_type = slug_to_type['website']

    for link in RelatedLink.objects.all().iterator():
        target_slug = LINK_TYPE_TO_RESOURCE_SLUG.get(link.link_type, 'website')
        resource_type = slug_to_type.get(target_slug, default_type)
        link.resource_type = resource_type
        link.save(update_fields=['resource_type'])


def reverse_migration(apps, schema_editor):
    UsefulLinkResourceType = apps.get_model('related_links', 'UsefulLinkResourceType')
    RelatedLink = apps.get_model('related_links', 'RelatedLink')

    RESOURCE_SLUG_TO_LINK_TYPE = {
        'website': 'website',
        'podcast': 'podcast',
        'video': 'video',
        'radio': 'radio',
        'social-media': 'social',
        'document-pdf': 'file',
    }

    for link in RelatedLink.objects.select_related('resource_type').iterator():
        if link.resource_type_id:
            link.link_type = RESOURCE_SLUG_TO_LINK_TYPE.get(
                link.resource_type.slug,
                'website',
            )
            link.save(update_fields=['link_type'])

    RelatedLink.objects.update(resource_type=None)
    UsefulLinkResourceType.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('related_links', '0006_usefullinkresourcetype'),
    ]

    operations = [
        migrations.RunPython(
            seed_resource_types_and_migrate_links,
            reverse_migration,
        ),
    ]
