# Generated manually for Django 4.2.18

import cloudinary.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0011_rename_ad_categories'),
    ]

    operations = [
        migrations.AddField(
            model_name='ad',
            name='extra_image_1',
            field=cloudinary.models.CloudinaryField(
                blank=True,
                help_text='Optional second image for the ad (will be shown in image carousel).',
                max_length=255,
                null=True,
                verbose_name='ad_extra_image_1'
            ),
        ),
        migrations.AddField(
            model_name='ad',
            name='extra_image_2',
            field=cloudinary.models.CloudinaryField(
                blank=True,
                help_text='Optional third image for the ad (will be shown in image carousel).',
                max_length=255,
                null=True,
                verbose_name='ad_extra_image_2'
            ),
        ),
    ]

