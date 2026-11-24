from django.db import migrations


RENAMED_CATEGORIES = {
    "work-services": (
        "خانه و ساختمان",
        "نظافت، باغبانی، بازسازی و خدمات ساختمان",
    ),
    "food-restaurant": (
        "رستوران و کافه",
        "رستوران، کافه، غذای بیرون‌بر و پذیرایی",
    ),
    "leisure": (
        "ورزش، هنر و سرگرمی",
        "باشگاه، فعالیت‌های هنری و تفریح خانوادگی",
    ),
}

NEW_CATEGORIES = {
    "vehicles-repair": ("خودرو و تعمیرگاه", "سرویس، تعمیر، لاستیک و معاینه فنی خودرو", 41),
    "transport-moving": ("حمل‌ونقل و اسباب‌کشی", "تاکسی، ترانسفر، جابه‌جایی و انبار", 42),
    "shops-shopping": ("فروشگاه و خرید", "مواد غذایی، پوشاک و لوازم خانه و باغ", 52),
    "travel-accommodation": ("سفر، اقامت و گردشگری", "هتل، هاستل و خدمات گردشگری", 92),
}

# Match reviewed listings by their public slugs within the original category.
# Leave other listings in place for editorial review.
LISTING_MOVES = {
    "work-services": {
        "vehicles-repair": (
            "peyvand-service-technical-17-20261006",
            "peyvand-service-technical-16-20261006",
            "dackia-hogsbo",
            "besikta-sisjon",
            "meca-olskroken-goteborg",
        ),
        "transport-moving": (
            "stadsbudet-stockholm",
            "shurgard-molndal",
            "sj-tagresor",
            "bergkvara-malmo",
            "vy-flygbussarna",
            "taxi97-malmo",
            "taxi-stockholm",
            "taxi-goteborg",
        ),
        "shops-shopping": (
            "peyvand-service-technical-19-20261006",
            "ahlens-nordstan",
            "byggmax-malmo",
            "rusta-backaplan",
            "mio-malmo",
            "jula-svagertorp",
            "biltema-sisjon",
            "bauhaus-sisjon-goteborg",
            "ikea-malmo",
        ),
        "health-welfare": ("arken-zoo-veterinar-malmo",),
        "ngmnh-o-rohh": ("fonus-heden-goteborg",),
    },
    "food-restaurant": {
        "shops-shopping": (
            "peyvand-service-food-22-20261006",
            "peyvand-service-food-21-20261006",
            "stora-coop-stadion-malmo",
            "ica-maxi-goteborg",
        ),
    },
    "leisure": {
        "travel-accommodation": (
            "peyvand-service-leisure-44-20261006",
            "peyvand-service-leisure-43-20261006",
            "peyvand-service-leisure-42-20261006",
            "peyvand-service-leisure-41-20261006",
            "elite-hotel-stockholm-plaza",
            "scandic-triangeln-malmo",
        ),
        "shops-shopping": ("lekia-nordstan",),
        "beauty-appliances": ("holistisk-massage",),
    },
}


def expand_directory(apps, schema_editor):
    database = schema_editor.connection.alias
    categories = apps.get_model("ads", "AdCategory").objects.using(database)
    ads = apps.get_model("ads", "Ad").objects.using(database)

    for slug, (name, description) in RENAMED_CATEGORIES.items():
        categories.filter(slug=slug).update(name=name, description=description)

    for slug, (name, description, order) in NEW_CATEGORIES.items():
        categories.get_or_create(
            slug=slug,
            defaults={"name": name, "description": description, "display_order": order},
        )

    category_ids = dict(categories.values_list("slug", "pk"))
    for source, destinations in LISTING_MOVES.items():
        for destination, slugs in destinations.items():
            if source in category_ids and destination in category_ids:
                ads.filter(category_id=category_ids[source], slug__in=slugs).update(
                    category_id=category_ids[destination],
                )


class Migration(migrations.Migration):
    dependencies = [("ads", "0020_rename_ads_adgalle_ad_id_6f0a0d_idx_ads_adgalle_ad_id_dcfdf3_idx")]
    operations = [migrations.RunPython(expand_directory)]
