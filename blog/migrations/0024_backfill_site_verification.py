# Generated migration to backfill site verification for existing users
from django.db import migrations
from django.utils import timezone


def backfill_site_verification(apps, schema_editor):
    """
    Backfill site verification for existing users.
    Mark users as verified if they have verified email addresses.
    """
    UserProfile = apps.get_model('blog', 'UserProfile')
    
    # Try to get EmailAddress model (may not exist in all setups)
    try:
        EmailAddress = apps.get_model('account', 'EmailAddress')
        # Get all users with verified emails
        verified_emails = EmailAddress.objects.filter(verified=True).values_list('user_id', flat=True)
        
        # Mark profiles as verified for users with verified emails
        UserProfile.objects.filter(
            user_id__in=verified_emails,
            is_site_verified=False
        ).update(
            is_site_verified=True,
            site_verified_at=timezone.now()
        )
    except LookupError:
        # EmailAddress model not found, skip backfill
        # Admin can manually verify users if needed
        pass


def reverse_backfill(apps, schema_editor):
    """Reverse migration - set all to unverified."""
    UserProfile = apps.get_model('blog', 'UserProfile')
    UserProfile.objects.update(is_site_verified=False, site_verified_at=None)


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0023_add_site_verification_fields'),
    ]

    operations = [
        migrations.RunPython(backfill_site_verification, reverse_backfill),
    ]

