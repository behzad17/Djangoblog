from django.core.management.base import BaseCommand

from notifications.tasks import backfill_notification_preferences as run_backfill


class Command(BaseCommand):
    help = 'Create NotificationPreference rows for users that do not have one.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print how many rows would be created without writing to the database.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        summary = run_backfill(dry_run=dry_run)

        mode = 'DRY RUN' if dry_run else 'LIVE'
        self.stdout.write(
            self.style.NOTICE(
                f'[{mode}] Notification preference backfill: '
                f'{summary["created"]} created, {summary["skipped"]} skipped (already existed).'
            )
        )
