from django.db import migrations


def set_site_domain(apps, schema_editor):
    Site = apps.get_model("sites", "Site")

    # If a Site with domain peyvand.se already exists (any ID), just
    # ensure its name is correct and exit to avoid unique constraint errors.
    existing = Site.objects.filter(domain="peyvand.se").first()
    if existing:
        if existing.name != "Peyvand":
            existing.name = "Peyvand"
            existing.save(update_fields=["name"])
        return

    # Otherwise, safely ensure Site with id=1 uses peyvand.se.
    site, created = Site.objects.get_or_create(
        id=1,
        defaults={"domain": "peyvand.se", "name": "Peyvand"},
    )
    if not created:
        site.domain = "peyvand.se"
        site.name = "Peyvand"
        site.save(update_fields=["domain", "name"])


def reverse_set_site_domain(apps, schema_editor):
    # Keep reverse migration safe; do not assume previous domain/name.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("sites", "0002_alter_domain_unique"),
        ("blog", "0030_fix_guide_questions_slug"),
    ]

    operations = [
        migrations.RunPython(set_site_domain, reverse_set_site_domain),
    ]

