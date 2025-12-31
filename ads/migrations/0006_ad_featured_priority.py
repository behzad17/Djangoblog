# Generated manually for Featured Priority feature
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0005_favoritead'),
    ]

    operations = [
        migrations.AddField(
            model_name='ad',
            name='featured_priority',
            field=models.PositiveIntegerField(
                blank=True,
                default=None,
                help_text='Priority for featured ads (1-39). Lower numbers appear first. Ads with priority 1-39 appear in top positions on page 1. Leave blank for automatic ordering by date.',
                null=True
            ),
        ),
    ]

