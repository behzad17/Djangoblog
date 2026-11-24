from django.db import migrations
from django.db.models import Q


def add_pet_services(apps, schema_editor):
    database = schema_editor.connection.alias
    categories = apps.get_model("ads", "AdCategory").objects.using(database)
    ads = apps.get_model("ads", "Ad").objects.using(database)

    category, _ = categories.get_or_create(
        slug="pet-services",
        defaults={
            "name": "حیوانات خانگی",
            "description": "دامپزشکی، پانسیون، آرایش، آموزش و لوازم حیوانات خانگی",
            "display_order": 86,
        },
    )
    ads.filter(category__slug="health-welfare").filter(
        Q(subcategory="veterinary")
        | Q(slug="arken-zoo-veterinar-malmo", subcategory="")
    ).update(category_id=category.pk, subcategory="veterinary")


class Migration(migrations.Migration):
    dependencies = [("ads", "0024_add_child_family_services")]
    operations = [migrations.RunPython(add_pet_services)]
