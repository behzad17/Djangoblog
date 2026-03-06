# Generated manually for WhatsApp URL field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('askme', '0004_moderator_instagram_url_moderator_linkedin_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='moderator',
            name='whatsapp_url',
            field=models.URLField(
                blank=True,
                help_text='WhatsApp link (e.g. https://wa.me/46701234567)',
                null=True,
                verbose_name='واتساپ'
            ),
        ),
    ]
