# Generated manually for Featured Ad feature
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0002_ad_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='ad',
            name='is_featured',
            field=models.BooleanField(default=False, help_text='Featured ads appear first in listings and have special highlighting.'),
        ),
        migrations.AddField(
            model_name='ad',
            name='featured_until',
            field=models.DateTimeField(blank=True, help_text='Optional: Featured status expires after this date. Leave blank for permanent featured status.', null=True),
        ),
    ]

