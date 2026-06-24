from django.urls import reverse

from .constants import IN_APP_MESSAGES, NotificationType
from .email import build_site_url
from .services import NotificationService


def notify_askme_specialist_answer(question):
    """Notify the asker that a specialist answered their question."""
    recipient = question.user
    if recipient is None:
        return None

    copy = IN_APP_MESSAGES[NotificationType.ASKME_SPECIALIST_ANSWER]
    url = build_site_url(reverse('my_questions'))

    return NotificationService.notify(
        recipient=recipient,
        notification_type=NotificationType.ASKME_SPECIALIST_ANSWER,
        title=copy['title'],
        message=copy['message'],
        url=url,
        actor=getattr(question.moderator, 'user', None),
        metadata={'question_id': question.id},
        send_email=True,
        email_context={
            'cta_url': url,
            'cta_text': 'مشاهده پاسخ متخصص',
        },
        dedup_key=f'question:{question.id}:answered',
    )


def notify_ad_approved(ad):
    """Notify the ad owner that their ad was approved."""
    if not ad.owner_id:
        return None

    copy = IN_APP_MESSAGES[NotificationType.AD_APPROVED]
    url = build_site_url(reverse('ads:ad_detail', args=[ad.slug]))

    return NotificationService.notify(
        recipient=ad.owner,
        notification_type=NotificationType.AD_APPROVED,
        title=copy['title'],
        message=copy['message'],
        url=url,
        metadata={'ad_id': ad.id},
        send_email=True,
        email_context={
            'ad_title': ad.title,
            'cta_url': url,
            'cta_text': 'مشاهده آگهی',
        },
    )


def notify_ad_rejected(ad):
    """Notify the ad owner that their ad was rejected via admin action."""
    if not ad.owner_id:
        return None

    copy = IN_APP_MESSAGES[NotificationType.AD_REJECTED]
    url = build_site_url(reverse('ads:edit_ad', args=[ad.slug]))

    return NotificationService.notify(
        recipient=ad.owner,
        notification_type=NotificationType.AD_REJECTED,
        title=copy['title'],
        message=copy['message'],
        url=url,
        metadata={'ad_id': ad.id},
        send_email=True,
        email_context={
            'ad_title': ad.title,
            'cta_url': url,
            'cta_text': 'ویرایش آگهی',
        },
    )


def notify_ad_upgraded_to_pro(ad):
    """Notify the ad owner that their ad was upgraded to Pro."""
    if not ad.owner_id:
        return None

    copy = IN_APP_MESSAGES[NotificationType.AD_PRO]
    url = build_site_url(reverse('ads:ad_detail', args=[ad.slug]))

    return NotificationService.notify(
        recipient=ad.owner,
        notification_type=NotificationType.AD_PRO,
        title=copy['title'],
        message=copy['message'],
        url=url,
        metadata={'ad_id': ad.id},
        send_email=True,
        email_context={
            'ad_title': ad.title,
            'cta_url': url,
            'cta_text': 'مشاهده آگهی',
        },
    )


def notify_ad_favorited(ad, actor):
    """Notify the ad owner that another user favorited their ad."""
    if not ad.owner_id or actor is None or ad.owner_id == actor.id:
        return None

    copy = IN_APP_MESSAGES[NotificationType.AD_FAVORITED]
    url = build_site_url(reverse('ads:ad_detail', args=[ad.slug]))

    return NotificationService.notify(
        recipient=ad.owner,
        notification_type=NotificationType.AD_FAVORITED,
        title=copy['title'],
        message=copy['message'],
        url=url,
        actor=actor,
        metadata={'ad_id': ad.id, 'favorited_by': actor.id},
        send_email=False,
    )


def notify_ad_expiring(ad, days=7):
    """Notify the ad owner that their ad expires in ``days`` days."""
    if not ad.owner_id:
        return None

    copy = IN_APP_MESSAGES[NotificationType.AD_EXPIRING]
    url = build_site_url(reverse('ads:my_ads'))
    dedup_key = f'ad:{ad.id}:expiring:{days}'

    return NotificationService.notify(
        recipient=ad.owner,
        notification_type=NotificationType.AD_EXPIRING,
        title=copy['title'],
        message=copy['message'],
        url=url,
        metadata={'ad_id': ad.id, 'days': days},
        send_email=True,
        email_context={
            'ad_title': ad.title,
            'cta_url': url,
            'cta_text': 'مدیریت آگهی',
        },
        dedup_key=dedup_key,
    )
