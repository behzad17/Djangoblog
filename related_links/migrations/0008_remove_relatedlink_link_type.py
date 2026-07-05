# Generated manually — remove legacy link_type and require resource_type

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('related_links', '0007_seed_usefullink_resource_types'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='relatedlink',
            name='link_type',
        ),
        migrations.AlterField(
            model_name='relatedlink',
            name='resource_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='links',
                to='related_links.usefullinkresourcetype',
                verbose_name='نوع منبع',
            ),
        ),
    ]
