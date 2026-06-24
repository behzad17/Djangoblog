import logging

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from ads.models import Ad
from askme.models import Question

from .dispatchers import (
    notify_ad_approved,
    notify_ad_upgraded_to_pro,
    notify_askme_specialist_answer,
)
from .services import NotificationService

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def create_notification_preferences(sender, instance, created, **kwargs):
    if created:
        NotificationService.get_or_create_preferences(instance)


@receiver(pre_save, sender=Question)
def capture_question_answer_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._was_answered = False
        return

    try:
        previous = Question.objects.only('answered').get(pk=instance.pk)
        instance._was_answered = previous.answered
    except Question.DoesNotExist:
        instance._was_answered = False


@receiver(post_save, sender=Question)
def question_answered_notification(sender, instance, created, **kwargs):
    if created:
        return

    was_answered = getattr(instance, '_was_answered', False)
    if was_answered or not instance.answered:
        return

    try:
        notify_askme_specialist_answer(instance)
    except Exception:
        logger.error(
            'Failed to send AskMe specialist answer notification for question %s',
            instance.pk,
            exc_info=True,
        )


@receiver(pre_save, sender=Ad)
def capture_ad_moderation_state(sender, instance, **kwargs):
    if not instance.pk:
        instance._was_approved = False
        instance._previous_plan = instance.plan
        return

    try:
        previous = Ad.objects.only('is_approved', 'plan').get(pk=instance.pk)
        instance._was_approved = previous.is_approved
        instance._previous_plan = previous.plan
    except Ad.DoesNotExist:
        instance._was_approved = False
        instance._previous_plan = instance.plan


@receiver(post_save, sender=Ad)
def ad_status_notification(sender, instance, created, **kwargs):
    if created:
        return

    was_approved = getattr(instance, '_was_approved', False)
    previous_plan = getattr(instance, '_previous_plan', instance.plan)

    try:
        if not was_approved and instance.is_approved:
            notify_ad_approved(instance)

        if previous_plan != 'pro' and instance.plan == 'pro':
            notify_ad_upgraded_to_pro(instance)
    except Exception:
        logger.error(
            'Failed to send ad status notification for ad %s',
            instance.pk,
            exc_info=True,
        )
