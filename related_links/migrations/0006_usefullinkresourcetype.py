# Generated manually — add UsefulLinkResourceType and nullable resource_type FK

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('related_links', '0005_relatedlink_short_description'),
    ]

    operations = [
        migrations.CreateModel(
            name='UsefulLinkResourceType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name_en', models.CharField(max_length=120, verbose_name='نام انگلیسی')),
                ('name_fa', models.CharField(max_length=120, verbose_name='نام فارسی')),
                ('slug', models.SlugField(max_length=120, unique=True, verbose_name='نامک')),
                ('icon', models.CharField(help_text='نام کلاس Bootstrap Icons، مثال: bi-globe', max_length=64, verbose_name='آیکون')),
                ('display_order', models.PositiveIntegerField(default=0, verbose_name='ترتیب نمایش')),
                ('is_active', models.BooleanField(default=True, verbose_name='فعال')),
                ('is_media', models.BooleanField(default=False, help_text='برای تمایز منابع رسانه\u200cای از منابع مرجع در رابط کاربری آینده.', verbose_name='رسانه')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='تاریخ ایجاد')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='تاریخ به\u200cروزرسانی')),
            ],
            options={
                'verbose_name': 'نوع منبع',
                'verbose_name_plural': 'انواع منبع',
                'ordering': ['display_order', 'name_en'],
            },
        ),
        migrations.AddField(
            model_name='relatedlink',
            name='resource_type',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='links',
                to='related_links.usefullinkresourcetype',
                verbose_name='نوع منبع',
            ),
        ),
    ]
