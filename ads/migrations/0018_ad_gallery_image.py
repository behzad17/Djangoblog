# Generated manually for Django 4.2.18

import cloudinary.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0017_adcategory_image'),
    ]

    operations = [
        migrations.CreateModel(
            name='AdGalleryImage',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('image', cloudinary.models.CloudinaryField(help_text='Optional gallery image for Pro ad detail pages.', max_length=255, verbose_name='ad_gallery')),
                ('sort_order', models.PositiveSmallIntegerField(default=0)),
                ('created_on', models.DateTimeField(auto_now_add=True)),
                ('ad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='gallery_images', to='ads.ad')),
            ],
            options={
                'verbose_name': 'Ad Gallery Image',
                'verbose_name_plural': 'Ad Gallery Images',
                'ordering': ['sort_order', 'id'],
                'indexes': [models.Index(fields=['ad', 'sort_order'], name='ads_adgalle_ad_id_6f0a0d_idx')],
            },
        ),
    ]
