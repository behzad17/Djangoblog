from django.core.management.base import BaseCommand

from notifications.tasks import send_expiring_ad_notifications


class Command(BaseCommand):
    help = 'Send 7-day ad expiration warnings to ad owners.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print actions without creating notifications or sending email.',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Days before expiration to warn (default: 7).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        summary = send_expiring_ad_notifications(days=days, dry_run=dry_run)

        mode = 'DRY RUN' if dry_run else 'LIVE'
        self.stdout.write(
            self.style.NOTICE(
                f'[{mode}] Ad expiration warnings ({days} days): '
                f'{summary["candidates"]} candidate(s), '
                f'{summary["sent"]} would send/send, '
                f'{summary["skipped_dedup"]} skipped (duplicate), '
                f'{summary["skipped_no_owner"]} skipped (no owner).'
            )
        )
