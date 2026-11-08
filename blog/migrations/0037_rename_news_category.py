from django.db import migrations


def rename_news_category(apps, schema_editor):
    Category = apps.get_model('blog', 'Category')
    Category.objects.using(schema_editor.connection.alias).filter(
        slug='news', name='News',
    ).update(name='اخبار')


class Migration(migrations.Migration):
    dependencies = [
        ('blog', '0036_post_event_city'),
    ]

    operations = [
        migrations.RunPython(rename_news_category, migrations.RunPython.noop),
    ]
