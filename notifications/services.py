import logging

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import QuerySet
from django.utils import timezone

from .constants import EMAIL_SUBJECTS, EMAIL_TEMPLATES
from .email import get_user_display_name, send_peyvand_email
from .models import Notification, NotificationPreference

logger = logging.getLogger(__name__)
User = get_user_model()


class NotificationService:
    """Single entry point for creating notifications and sending emails."""

    @staticmethod
    def get_or_create_preferences(user) -> NotificationPreference:
        preferences, _ = NotificationPreference.objects.get_or_create(user=user)
        return preferences

    @staticmethod
    def _dedup_exists(recipient, notification_type: str, dedup_key: str) -> bool:
        return Notification.objects.filter(
            recipient=recipient,
            notification_type=notification_type,
            metadata__dedup_key=dedup_key,
        ).exists()

    @staticmethod
    def notify(
        *,
        recipient,
        notification_type: str,
        title: str,
        message: str,
        url: str = '',
        actor=None,
        metadata: dict | None = None,
        send_email: bool = False,
        email_template: str | None = None,
        email_context: dict | None = None,
        email_subject: str | None = None,
        dedup_key: str | None = None,
        create_in_app: bool = True,
    ) -> Notification | None:
        """
        Create an in-app notification and optionally queue a transactional email.

        Weekly digest and other email-only flows should pass ``create_in_app=False``.
        """
        if recipient is None:
            return None

        metadata = dict(metadata or {})
        if dedup_key:
            metadata['dedup_key'] = dedup_key
            if create_in_app and NotificationService._dedup_exists(
                recipient, notification_type, dedup_key
            ):
                logger.info(
                    'Skipping duplicate notification %s for user %s',
                    notification_type,
                    recipient.pk,
                )
                return None

        preferences = NotificationService.get_or_create_preferences(recipient)

        notification = None
        if create_in_app:
            if not preferences.allows_in_app(notification_type):
                logger.info(
                    'In-app notification disabled for %s (user %s)',
                    notification_type,
                    recipient.pk,
                )
            else:
                notification = Notification.objects.create(
                    recipient=recipient,
                    actor=actor,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    url=url,
                    metadata=metadata,
                )

        should_send_email = send_email and bool(getattr(recipient, 'email', ''))
        if should_send_email and not preferences.allows_email(notification_type):
            should_send_email = False

        if should_send_email:
            template = email_template or EMAIL_TEMPLATES.get(notification_type)
            subject = email_subject or EMAIL_SUBJECTS.get(notification_type, title)
            context = {
                'user_name': get_user_display_name(recipient),
                **(email_context or {}),
            }

            def _send_email() -> None:
                try:
                    send_peyvand_email(
                        to=recipient.email,
                        subject=subject,
                        template_base=template,
                        context=context,
                    )
                    if notification is not None:
                        notification.email_sent = True
                        notification.email_sent_at = timezone.now()
                        notification.save(update_fields=['email_sent', 'email_sent_at'])
                except Exception:
                    logger.error(
                        'Failed to send %s email to user %s',
                        notification_type,
                        recipient.pk,
                        exc_info=True,
                    )

            transaction.on_commit(_send_email)

        return notification

    @staticmethod
    def send_email_only(
        *,
        recipient,
        notification_type: str,
        email_context: dict | None = None,
        email_template: str | None = None,
        email_subject: str | None = None,
    ) -> bool:
        """Send a preference-aware email without creating an in-app notification."""
        preferences = NotificationService.get_or_create_preferences(recipient)
        if not preferences.allows_email(notification_type):
            return False
        if not getattr(recipient, 'email', ''):
            return False

        template = email_template or EMAIL_TEMPLATES.get(notification_type)
        subject = email_subject or EMAIL_SUBJECTS.get(notification_type, 'پیوند')
        context = {
            'user_name': get_user_display_name(recipient),
            **(email_context or {}),
        }

        try:
            return send_peyvand_email(
                to=recipient.email,
                subject=subject,
                template_base=template,
                context=context,
            )
        except Exception:
            logger.error(
                'Failed to send email-only %s to user %s',
                notification_type,
                recipient.pk,
                exc_info=True,
            )
            return False

    @staticmethod
    def get_unread_count(user) -> int:
        if not user.is_authenticated:
            return 0
        return Notification.objects.filter(recipient=user, is_read=False).count()

    @staticmethod
    def get_recent(user, limit: int = 10) -> QuerySet:
        return (
            Notification.objects.filter(recipient=user)
            .select_related('actor')
            .order_by('-created_at')[:limit]
        )

    @staticmethod
    def mark_read(notification_id: int, user) -> bool:
        updated = Notification.objects.filter(
            pk=notification_id,
            recipient=user,
            is_read=False,
        ).update(is_read=True)
        return updated > 0

    @staticmethod
    def mark_all_read(user) -> int:
        return Notification.objects.filter(recipient=user, is_read=False).update(
            is_read=True
        )
