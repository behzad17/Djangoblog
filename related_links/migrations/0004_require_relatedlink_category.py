# Generated manually for Phase 1 — require category after data seed

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('related_links', '0003_seed_usefullink_categories'),
    ]

    operations = [
        migrations.AlterField(
            model_name='relatedlink',
            name='category',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name='links',
                to='related_links.usefullinkcategory',
                verbose_name='دسته\u200cبندی',
            ),
        ),
    ]
