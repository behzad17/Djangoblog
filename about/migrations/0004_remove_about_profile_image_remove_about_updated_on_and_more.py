# Generated by Django 4.2.18 on 2025-06-12 22:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('about', '0003_about_profile_image_alter_about_title'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='about',
            name='profile_image',
        ),
        migrations.RemoveField(
            model_name='about',
            name='updated_on',
        ),
        migrations.AlterField(
            model_name='about',
            name='title',
            field=models.CharField(max_length=200),
        ),
        migrations.AlterField(
            model_name='collaboraterequest',
            name='name',
            field=models.CharField(max_length=100),
        ),
    ]
