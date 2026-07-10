from django.db.models.signals import post_save
from django.dispatch import receiver

from community.models import Reply


@receiver(post_save, sender=Reply)
def notify_discussion_author_on_reply(sender, instance, created, **kwargs):
    if not instance.approved:
        return
    from notifications.dispatchers import notify_community_reply

    notify_community_reply(instance)
