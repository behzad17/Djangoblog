from django.db import migrations


def set_site_domain(apps, schema_editor):
    Site = apps.get_model("sites", "Site")

    site, created = Site.objects.get_or_create(
        id=1,
        defaults={"domain": "peyvand.se", "name": "Peyvand"},
    )
    site.domain = "peyvand.se"
    site.name = "Peyvand"
    site.save()


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

