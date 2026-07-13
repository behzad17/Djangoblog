from django.core.management.base import BaseCommand, CommandError

from notifications.tasks import send_weekly_digest


class Command(BaseCommand):
    help = 'Send the weekly digest email to opted-in users.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Print actions without sending email.',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            default=None,
            help='Send only to a specific user ID (useful for testing).',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_id = options['user_id']

        summary = send_weekly_digest(dry_run=dry_run, user_id=user_id)

        if summary.get('skipped_weekday'):
            self.stdout.write(
                self.style.WARNING(
                    f'Weekly digest skipped: today is {summary["weekday"]}; '
                    'digest sends on Friday only.'
                )
            )
            return

        stats = summary['stats']

        if user_id is not None and summary['recipients'] == 0:
            raise CommandError(f'No eligible digest recipient found for user {user_id}.')

        mode = 'DRY RUN' if dry_run else 'LIVE'
        self.stdout.write(
            self.style.NOTICE(
                f'[{mode}] Weekly digest {summary["period_start"]} → {summary["period_end"]}: '
                f'{summary["recipients"]} recipient(s), {summary["sent"]} sent.'
            )
        )
        self.stdout.write(
            f'  articles={stats["new_articles"]}, '
            f'events={stats["new_events"]}, '
            f'businesses={stats["new_businesses"]}, '
            f'pro_ads={stats["new_pro_ads"]}'
        )
