from django.db import migrations


# Assign only listings whose advertised service was reviewed.
LISTINGS = {
    "work-services": {
        "cleaning": ("peyvand-service-technical-20-20261006", "hemfrid-stockholm", "homemaid-goteborg"),
        "building": ("peab-malmo", "skanska-malmo"),
        "pest-control": ("anticimex-stockholm",),
        "home-help": ("peyvand-service-technical-18-20261006", "mynanny-stockholm"),
    },
    "vehicles-repair": {
        "car-repair": ("peyvand-service-technical-17-20261006", "meca-olskroken-goteborg"),
        "body-glass": ("peyvand-service-technical-16-20261006",),
        "tires": ("dackia-hogsbo",),
        "inspection": ("besikta-sisjon",),
    },
    "transport-moving": {
        "moving": ("stadsbudet-stockholm", "shurgard-molndal"),
        "taxi": ("taxi97-malmo", "taxi-stockholm", "taxi-goteborg", "vy-flygbussarna"),
        "group-transport": ("sj-tagresor", "bergkvara-malmo"),
    },
    "food-restaurant": {
        "restaurants": ("peyvand-service-food-25-20261006", "peyvand-service-food-23-20261006"),
        "cafes": ("peyvand-service-food-24-20261006",),
    },
    "shops-shopping": {
        "groceries": (
            "peyvand-service-food-22-20261006", "peyvand-service-food-21-20261006",
            "stora-coop-stadion-malmo", "ica-maxi-goteborg",
        ),
        "home-goods": ("rusta-backaplan", "mio-malmo", "ikea-malmo"),
        "tools": ("peyvand-service-technical-19-20261006", "byggmax-malmo", "jula-svagertorp", "bauhaus-sisjon-goteborg"),
        "clothing": ("ahlens-nordstan",),
        "car-accessories": ("biltema-sisjon",),
        "toys": ("lekia-nordstan",),
    },
    "health-welfare": {"veterinary": ("arken-zoo-veterinar-malmo",)},
    "beauty-appliances": {"massage": ("holistisk-massage",)},
    "travel-accommodation": {
        "hotels": (
            "peyvand-service-leisure-44-20261006", "peyvand-service-leisure-43-20261006",
            "peyvand-service-leisure-42-20261006", "peyvand-service-leisure-41-20261006",
            "elite-hotel-stockholm-plaza", "scandic-triangeln-malmo",
        ),
    },
    "leisure": {
        "sports": ("nordic-wellness-folkets-park-malmo",),
        "arts": ("peyvand-service-leisure-45-20261006", "universeum-goteborg", "grona-lund-stockholm", "liseberg-goteborg"),
    },
}


def seed_subcategories(apps, schema_editor):
    database = schema_editor.connection.alias
    category = apps.get_model("ads", "AdCategory")
    ad = apps.get_model("ads", "Ad")
    category.objects.using(database).get_or_create(
        slug="housing-real-estate",
        defaults={
            "name": "مسکن و املاک",
            "description": "مشاور املاک، اجاره و خرید، و مدیریت ملک",
            "display_order": 91,
        },
    )
    for category_slug, subcategories in LISTINGS.items():
        for subcategory, slugs in subcategories.items():
            ad.objects.using(database).filter(
                category__slug=category_slug, slug__in=slugs, subcategory="",
            ).update(subcategory=subcategory)


class Migration(migrations.Migration):
    dependencies = [("ads", "0022_ad_subcategory")]
    operations = [migrations.RunPython(seed_subcategories)]
