from django.db import migrations


def rename_ad_categories(apps, schema_editor):
    """
    Rename existing AdCategory records (names + some slugs) to the new taxonomy.

    This is written to be idempotent and safe on already-migrated databases.
    """
    AdCategory = apps.get_model("ads", "AdCategory")

    # Mapping keyed by old slug; we also check old name for extra safety.
    mappings = [
        {
            "old_slug": "vehicles",
            "old_name": "رفت‌ وآمد و وسایل نقلیه",
            "new_name": "خدمات مالی",
            "new_slug": "economi",
        },
        {
            "old_slug": "housing",
            "old_name": "مسکن و زندگی روزمره",
            "new_name": "خدمات اداری و اجتماعی",
            "new_slug": "social-zendegi",
        },
        {
            "old_slug": "work-services",
            "old_name": "کار و همراهی حرفه‌ای",
            "new_name": "خدمات شغلی و حرفه‌ای",
            "new_slug": "work-services",
        },
        {
            "old_slug": "leisure",
            "old_name": "اوقات فراغت و زندگی اجتماعی",
            "new_name": "رفاه و سرگرمی",
            "new_slug": "leisure",
        },
        {
            "old_slug": "food-restaurant",
            "old_name": "غذا، طعم و فرهنگ",
            "new_name": "رستوران، کافه و مواد غذایی",
            "new_slug": "food-restaurant",
        },
        {
            "old_slug": "health-welfare",
            "old_name": "سلامت، رفاه و مراقبت",
            "new_name": "خدمات پزشکی و سلامت",
            "new_slug": "health-welfare",
        },
        {
            "old_slug": "home-appliances",
            "old_name": "خانه و وسایل زندگی",
            "new_name": "بهداشت و زیبایی",
            "new_slug": "beauty-appliances",
        },
        {
            "old_slug": "legal-financial",
            "old_name": "خدمات حقوقی و مالی سوئد",
            "new_name": "خدمات حقوقی",
            "new_slug": "legal-financial",
        },
        {
            "old_slug": "mozsh-zbn-o-dr",
            "old_name": "آموزش، زبان و یادگیری",
            "new_name": "خدمات آموزشی",
            "new_slug": "mozsh-zbn-o-dr",
        },
        {
            "old_slug": "fnor-o-khdmt-dgtl",
            "old_name": "فناوری و خدمات دیجیتال",
            "new_name": "فناوری و توسعه وب",
            "new_slug": "fnor-o-khdmt-dgtl",
        },
    ]

    for m in mappings:
        qs = AdCategory.objects.filter(slug=m["old_slug"])
        if m["old_name"]:
            qs = qs | AdCategory.objects.filter(name=m["old_name"])
        for cat in qs.distinct():
            # If already migrated, skip
            if cat.name == m["new_name"] and cat.slug == m["new_slug"]:
                continue
            cat.name = m["new_name"]
            cat.slug = m["new_slug"]
            cat.save()


def reverse_rename_ad_categories(apps, schema_editor):
    """
    Best-effort reverse migration to restore original names/slugs.
    """
    AdCategory = apps.get_model("ads", "AdCategory")

    reverse_mappings = [
        {
            "new_slug": "economi",
            "new_name": "خدمات مالی",
            "old_name": "رفت‌ وآمد و وسایل نقلیه",
            "old_slug": "vehicles",
        },
        {
            "new_slug": "social-zendegi",
            "new_name": "خدمات اداری و اجتماعی",
            "old_name": "مسکن و زندگی روزمره",
            "old_slug": "housing",
        },
        {
            "new_slug": "work-services",
            "new_name": "خدمات شغلی و حرفه‌ای",
            "old_name": "کار و همراهی حرفه‌ای",
            "old_slug": "work-services",
        },
        {
            "new_slug": "leisure",
            "new_name": "رفاه و سرگرمی",
            "old_name": "اوقات فراغت و زندگی اجتماعی",
            "old_slug": "leisure",
        },
        {
            "new_slug": "food-restaurant",
            "new_name": "رستوران، کافه و مواد غذایی",
            "old_name": "غذا، طعم و فرهنگ",
            "old_slug": "food-restaurant",
        },
        {
            "new_slug": "health-welfare",
            "new_name": "خدمات پزشکی و سلامت",
            "old_name": "سلامت، رفاه و مراقبت",
            "old_slug": "health-welfare",
        },
        {
            "new_slug": "beauty-appliances",
            "new_name": "بهداشت و زیبایی",
            "old_name": "خانه و وسایل زندگی",
            "old_slug": "home-appliances",
        },
        {
            "new_slug": "legal-financial",
            "new_name": "خدمات حقوقی",
            "old_name": "خدمات حقوقی و مالی سوئد",
            "old_slug": "legal-financial",
        },
        {
            "new_slug": "mozsh-zbn-o-dr",
            "new_name": "خدمات آموزشی",
            "old_name": "آموزش، زبان و یادگیری",
            "old_slug": "mozsh-zbn-o-dr",
        },
        {
            "new_slug": "fnor-o-khdmt-dgtl",
            "new_name": "فناوری و توسعه وب",
            "old_name": "فناوری و خدمات دیجیتال",
            "old_slug": "fnor-o-khdmt-dgtl",
        },
    ]

    for m in reverse_mappings:
        qs = AdCategory.objects.filter(slug=m["new_slug"])
        if m["new_name"]:
            qs = qs | AdCategory.objects.filter(name=m["new_name"])
        for cat in qs.distinct():
            cat.name = m["old_name"]
            cat.slug = m["old_slug"]
            cat.save()


class Migration(migrations.Migration):

    dependencies = [
        ("ads", "0010_adsviewcount"),
    ]

    operations = [
        migrations.RunPython(rename_ad_categories, reverse_rename_ad_categories),
    ]


