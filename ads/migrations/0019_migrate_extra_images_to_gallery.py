from django.db import migrations


def migrate_extra_images_to_gallery(apps, schema_editor):
    Ad = apps.get_model('ads', 'Ad')
    AdGalleryImage = apps.get_model('ads', 'AdGalleryImage')

    for ad in Ad.objects.all().iterator():
        sort_order = 0
        if ad.extra_image_1:
            AdGalleryImage.objects.create(
                ad_id=ad.pk,
                image=ad.extra_image_1,
                sort_order=sort_order,
            )
            sort_order += 1
        if ad.extra_image_2:
            AdGalleryImage.objects.create(
                ad_id=ad.pk,
                image=ad.extra_image_2,
                sort_order=sort_order,
            )


def reverse_migrate_extra_images_to_gallery(apps, schema_editor):
    Ad = apps.get_model('ads', 'Ad')
    AdGalleryImage = apps.get_model('ads', 'AdGalleryImage')

    for ad in Ad.objects.all().iterator():
        gallery_images = list(
            AdGalleryImage.objects.filter(ad_id=ad.pk).order_by('sort_order', 'id')
        )
        if gallery_images:
            ad.extra_image_1 = gallery_images[0].image
        if len(gallery_images) > 1:
            ad.extra_image_2 = gallery_images[1].image
        ad.save(update_fields=['extra_image_1', 'extra_image_2'])
        AdGalleryImage.objects.filter(ad_id=ad.pk).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0018_ad_gallery_image'),
    ]

    operations = [
        migrations.RunPython(
            migrate_extra_images_to_gallery,
            reverse_migrate_extra_images_to_gallery,
        ),
    ]
