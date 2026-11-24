from django.db import migrations


def add_celebration_services(apps, schema_editor):
    database = schema_editor.connection.alias
    categories = apps.get_model("ads", "AdCategory").objects.using(database)
    ads = apps.get_model("ads", "Ad").objects.using(database)

    category, _ = categories.get_or_create(
        slug="celebration-services",
        defaults={
            "name": "مراسم و جشن‌ها",
            "description": "سالن، عکاسی، موسیقی، سفرهٔ عقد، گل‌آرایی و پذیرایی برای مراسم",
            "display_order": 87,
        },
    )
    ads.filter(category__slug="leisure", subcategory="events").update(
        category_id=category.pk,
        subcategory="event-planning",
    )


class Migration(migrations.Migration):
    dependencies = [("ads", "0025_add_pet_services")]
    operations = [migrations.RunPython(add_celebration_services)]
