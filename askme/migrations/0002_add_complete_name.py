# Generated manually
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('askme', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='moderator',
            name='complete_name',
            field=models.CharField(blank=True, help_text="Complete/full name to display in Ask Me boxes (if empty, will use user's full name or username)", max_length=200),
        ),
    ]

