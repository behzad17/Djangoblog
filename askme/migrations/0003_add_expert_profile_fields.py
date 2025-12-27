# Generated manually for Expert Profile feature
from django.db import migrations, models
from django.utils.text import slugify


def drop_existing_indexes(apps, schema_editor):
    """
    Drop any existing indexes on slug column from previous failed migrations.
    """
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS askme_moderator_slug_9dcc5146_like;")
        cursor.execute("DROP INDEX IF EXISTS askme_moderator_slug_idx;")
        cursor.execute("DROP INDEX IF EXISTS askme_moderator_slug_unique;")
        # Also check for any other slug-related indexes
        cursor.execute("""
            SELECT indexname FROM pg_indexes 
            WHERE tablename = 'askme_moderator' 
            AND indexname LIKE '%slug%';
        """)
        for row in cursor.fetchall():
            cursor.execute(f"DROP INDEX IF EXISTS {row[0]};")


def populate_slugs(apps, schema_editor):
    """
    Data migration to populate slugs for existing moderators.
    """
    Moderator = apps.get_model('askme', 'Moderator')
    
    for moderator in Moderator.objects.all():
        # Check if slug is empty or None
        current_slug = getattr(moderator, 'slug', None) or ''
        if not current_slug:
            # Generate slug from display name or username
            display_name = moderator.complete_name or moderator.user.get_full_name() or moderator.user.username
            base_slug = slugify(display_name)
            if not base_slug:
                base_slug = slugify(moderator.user.username)
            
            # Ensure uniqueness
            slug = base_slug
            counter = 1
            while Moderator.objects.filter(slug=slug).exclude(pk=moderator.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            moderator.slug = slug
            moderator.save(update_fields=['slug'])


def reverse_populate_slugs(apps, schema_editor):
    """
    Reverse migration - clear slugs (optional, for rollback)
    """
    Moderator = apps.get_model('askme', 'Moderator')
    Moderator.objects.all().update(slug='')


class Migration(migrations.Migration):

    dependencies = [
        ('askme', '0002_add_complete_name'),
    ]

    operations = [
        # Drop any existing indexes on slug column first
        migrations.RunPython(drop_existing_indexes, migrations.RunPython.noop),
        migrations.AddField(
            model_name='moderator',
            name='field_specialty',
            field=models.CharField(
                blank=True,
                help_text="Field/Specialty domain (e.g., 'Legal', 'Medical', 'Financial')",
                max_length=200
            ),
        ),
        migrations.AddField(
            model_name='moderator',
            name='disclaimer',
            field=models.TextField(
                blank=True,
                help_text='Custom disclaimer text for this expert (shown on profile page)'
            ),
        ),
        # Add slug field without unique constraint first (to allow population)
        # Note: Django may create a LIKE index automatically, which we'll drop after
        migrations.AddField(
            model_name='moderator',
            name='slug',
            field=models.SlugField(
                blank=True,
                help_text='URL-friendly identifier for expert profile page',
                max_length=200,
                db_index=False  # Prevent automatic index creation
            ),
        ),
        # Drop any index Django might have created automatically (in case db_index=False didn't work)
        migrations.RunSQL(
            sql=[
                "DROP INDEX IF EXISTS askme_moderator_slug_9dcc5146_like;",
                "DROP INDEX IF EXISTS askme_moderator_slug_idx;",
            ],
            reverse_sql=migrations.RunSQL.noop,
        ),
        # Populate slugs for existing records
        migrations.RunPython(populate_slugs, reverse_populate_slugs),
        # Now add unique constraint (all slugs should be populated and unique)
        migrations.AlterField(
            model_name='moderator',
            name='slug',
            field=models.SlugField(
                blank=True,
                help_text='URL-friendly identifier for expert profile page',
                max_length=200,
                unique=True
            ),
        ),
    ]

