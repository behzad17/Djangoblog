from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("blog", "0035_alter_post_title_non_unique")]
    operations = [migrations.AddField(
        model_name="post", name="event_city",
        field=models.CharField(blank=True, max_length=100, help_text="City only, shown on homepage event cards. Keep venue/address in location."),
    )]
