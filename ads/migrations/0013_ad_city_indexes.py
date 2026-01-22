# Generated manually for Django 4.2.18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0012_ad_extra_images'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='ad',
            index=models.Index(fields=['city'], name='ads_ad_city_idx'),
        ),
        migrations.AddIndex(
            model_name='ad',
            index=models.Index(fields=['category', 'city'], name='ads_ad_category_city_idx'),
        ),
    ]

