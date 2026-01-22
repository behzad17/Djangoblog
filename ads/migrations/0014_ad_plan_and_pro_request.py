# Generated manually for Django 4.2.18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ads', '0013_ad_city_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='ad',
            name='plan',
            field=models.CharField(
                choices=[('free', 'Free'), ('pro', 'Pro')],
                default='free',
                help_text='Ad plan type: Free or Pro',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='ad',
            name='pro_requested',
            field=models.BooleanField(
                default=False,
                help_text='Whether the user has requested Pro upgrade',
            ),
        ),
        migrations.AddField(
            model_name='ad',
            name='pro_request_phone',
            field=models.CharField(
                blank=True,
                help_text='Phone number provided when requesting Pro upgrade',
                max_length=30,
                null=True,
            ),
        ),
        migrations.AddField(
            model_name='ad',
            name='pro_requested_at',
            field=models.DateTimeField(
                blank=True,
                help_text='When the Pro upgrade was requested',
                null=True,
            ),
        ),
    ]

