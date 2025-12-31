"""
Signals for askme app - admin notifications.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


from .models import Question

@receiver(post_save, sender=Question)
def notify_admin_new_question(sender, instance, created, **kwargs):
    """Send email to admin when new question is created."""
    if not created:
        return  # Only on creation
    
    # Only notify for unanswered questions
    if instance.answered:
        return
    
    # Check if notifications are enabled
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    if not admin_email:
        logger.warning("ADMIN_EMAIL not set, skipping question notification")
        return
    
    admin_notification_enabled = getattr(settings, 'ADMIN_NOTIFICATION_ENABLED', True)
    if not admin_notification_enabled:
        return
    
    try:
        # Get site URL for admin link
        try:
            site = Site.objects.get_current()
            site_domain = site.domain
            if not site_domain.startswith('http'):
                protocol = 'https' if not settings.DEBUG else 'http'
                site_url = f"{protocol}://{site_domain}"
            else:
                site_url = site_domain
        except Exception:
            site_url = ''
        
        admin_question_url = f"{site_url}/admin/askme/question/{instance.id}/" if site_url else f"/admin/askme/question/{instance.id}/"
        
        moderator_name = instance.moderator.user.username if instance.moderator else "Unassigned"
        
        subject = f"New Question Submitted: User {instance.user.username}"
        message = f"""
A new question has been submitted:

User: {instance.user.username}
Moderator: {moderator_name}
Created: {instance.created_on.strftime('%Y-%m-%d %H:%M')}

Note: Question/answer content is not shown for privacy. Review metadata at:
{admin_question_url}
"""
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin_email],
            fail_silently=False,
        )
        
        logger.info(f"Admin notification sent for new question: {instance.id}")
    except Exception as e:
        logger.error(f"Error sending admin notification for new question: {e}", exc_info=True)

