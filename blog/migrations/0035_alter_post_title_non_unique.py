from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0034_category_display_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='post',
            name='title',
            field=models.CharField(max_length=200),
        ),
    ]
