from django.db import migrations


def add_child_family_services(apps, schema_editor):
    database = schema_editor.connection.alias
    categories = apps.get_model("ads", "AdCategory").objects.using(database)
    ads = apps.get_model("ads", "Ad").objects.using(database)

    category, _ = categories.get_or_create(
        slug="child-family-services",
        defaults={
            "name": "خدمات کودک و خانواده",
            "description": "نگهداری کودک، کمک‌درسی، فعالیت‌های بعد از مدرسه و حمایت از والدین",
            "display_order": 85,
        },
    )
    ads.filter(
        slug="mynanny-stockholm",
        category__slug="work-services",
        subcategory__in=("", "home-help"),
    ).update(category_id=category.pk, subcategory="childcare")


class Migration(migrations.Migration):
    dependencies = [("ads", "0023_seed_directory_subcategories")]
    operations = [migrations.RunPython(add_child_family_services)]
