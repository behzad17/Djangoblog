import logging
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone

from ads.models import Ad

from .constants import NotificationType
from .dispatchers import notify_ad_expiring
from .services import NotificationService
from .weekly_digest import (
    build_weekly_digest_email_context,
    build_weekly_digest_stats,
    get_weekly_digest_period,
    get_weekly_digest_recipients,
    is_weekly_digest_send_day,
)

User = get_user_model()
logger = logging.getLogger(__name__)

# Re-exported for tests and management command output.
__all__ = [
    'build_weekly_digest_stats',
    'get_weekly_digest_period',
    'get_weekly_digest_recipients',
    'is_weekly_digest_send_day',
    'send_weekly_digest',
]


def get_expiring_ads(days=7):
    """Return active approved ads expiring in exactly ``days`` from today."""
    target_date = timezone.localdate() + timedelta(days=days)
    return (
        Ad.objects.filter(
            end_date=target_date,
            is_approved=True,
            is_active=True,
            owner__isnull=False,
        )
        .select_related('owner')
        .order_by('id')
    )


def send_expiring_ad_notifications(*, days=7, dry_run=False):
    """
    Notify ad owners that their ad expires in ``days`` days.

    Returns a summary dict for logging and management command output.
    """
    ads = list(get_expiring_ads(days=days))
    summary = {
        'days': days,
        'candidates': len(ads),
        'sent': 0,
        'skipped_dedup': 0,
        'skipped_no_owner': 0,
        'dry_run': dry_run,
    }

    for ad in ads:
        if not ad.owner_id:
            summary['skipped_no_owner'] += 1
            continue

        dedup_key = f'ad:{ad.id}:expiring:{days}'
        if NotificationService._dedup_exists(
            ad.owner,
            NotificationType.AD_EXPIRING,
            dedup_key,
        ):
            summary['skipped_dedup'] += 1
            continue

        if dry_run:
            summary['sent'] += 1
            continue

        notification = notify_ad_expiring(ad, days=days)
        if notification is not None:
            summary['sent'] += 1

    return summary


def send_weekly_digest(*, dry_run=False, user_id=None):
    """
    Send the weekly digest email to opted-in users.

    Email-only: no in-app Notification rows are created.
    Sends on Friday only (local timezone); other days exit without sending.
    """
    today = timezone.localdate()
    if not is_weekly_digest_send_day(today):
        logger.info(
            'Skipping weekly digest: today is %s (%s); digest sends on Friday only.',
            today.isoformat(),
            today.strftime('%A'),
        )
        return {
            'skipped_weekday': True,
            'weekday': today.strftime('%A'),
            'period_start': None,
            'period_end': None,
            'recipients': 0,
            'sent': 0,
            'skipped_preference': 0,
            'dry_run': dry_run,
            'stats': None,
        }

    period_start, period_end = get_weekly_digest_period()
    stats = build_weekly_digest_stats(period_start, period_end)
    recipients = list(get_weekly_digest_recipients(user_id=user_id))

    summary = {
        'skipped_weekday': False,
        'weekday': today.strftime('%A'),
        'period_start': period_start.isoformat(),
        'period_end': period_end.isoformat(),
        'recipients': len(recipients),
        'sent': 0,
        'skipped_preference': 0,
        'dry_run': dry_run,
        'stats': stats,
    }

    email_context = build_weekly_digest_email_context(period_start, period_end)

    for user in recipients:
        preferences = getattr(user, 'notification_preferences', None)
        if preferences is None or not preferences.weekly_digest:
            summary['skipped_preference'] += 1
            continue

        if dry_run:
            summary['sent'] += 1
            continue

        sent = NotificationService.send_email_only(
            recipient=user,
            notification_type=NotificationType.WEEKLY_DIGEST,
            email_context=email_context,
        )
        if sent:
            summary['sent'] += 1

    return summary


def backfill_notification_preferences(*, dry_run=False):
    """
    Create ``NotificationPreference`` rows for users that do not have one.

    Safe to run multiple times; idempotent.
    """
    users_without = User.objects.filter(notification_preferences__isnull=True).order_by('id')
    skipped = User.objects.filter(notification_preferences__isnull=False).count()
    created = 0

    for user in users_without.iterator():
        if dry_run:
            created += 1
            continue
        NotificationService.get_or_create_preferences(user)
        created += 1

    return {
        'created': created,
        'skipped': skipped,
        'dry_run': dry_run,
    }
