from django.db import migrations


def add_nightlife(apps, schema_editor):
    categories = apps.get_model("ads", "AdCategory")
    categories.objects.using(schema_editor.connection.alias).get_or_create(
        slug="nightlife",
        defaults={
            "name": "بار و کلوب شبانه",
            "description": "بار، کلوب شبانه، دیسکو و سالن رقص در سوئد",
            "display_order": 88,
        },
    )


class Migration(migrations.Migration):
    dependencies = [("ads", "0027_ad_address_note_ad_postal_address")]
    operations = [migrations.RunPython(add_nightlife)]
