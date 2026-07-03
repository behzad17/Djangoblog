"""
Signals for ads app - admin notifications and Cloudinary cleanup.
"""
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


from .cloudinary_cleanup import destroy_cloudinary_asset
from .models import Ad, AdGalleryImage


@receiver(pre_delete, sender=AdGalleryImage)
def delete_gallery_image_asset(sender, instance, **kwargs):
    """Remove gallery image from Cloudinary when the row is deleted."""
    destroy_cloudinary_asset(instance.image)


@receiver(pre_delete, sender=Ad)
def delete_ad_primary_image_asset(sender, instance, **kwargs):
    """Remove primary ad image from Cloudinary when the ad is deleted."""
    destroy_cloudinary_asset(instance.image)


@receiver(post_save, sender=Ad)
def notify_admin_new_ad(sender, instance, created, **kwargs):
    """Send email to admin when new ad is created and needs approval."""
    if not created:
        return  # Only on creation
    
    # Only notify if ad is not approved
    if instance.is_approved:
        return
    
    # Check if notifications are enabled
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    if not admin_email:
        logger.warning("ADMIN_EMAIL not set, skipping ad notification")
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
        
        admin_ad_url = f"{site_url}/admin/ads/ad/{instance.id}/" if site_url else f"/admin/ads/ad/{instance.id}/"
        
        subject = f"New Ad Requires Approval: {instance.title[:50]}"
        message = f"""
A new ad has been submitted and requires approval:

Title: {instance.title}
Owner: {instance.owner.username}
Category: {instance.category.name}
Created: {instance.created_on.strftime('%Y-%m-%d %H:%M')}

Review at: {admin_ad_url}
"""
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin_email],
            fail_silently=False,
        )
        
        logger.info(f"Admin notification sent for new ad: {instance.id}")
    except Exception as e:
        logger.error(f"Error sending admin notification for new ad: {e}", exc_info=True)


def notify_admin_pro_request(ad):
    """Send email to admin when a user requests Pro upgrade for an ad."""
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    if not admin_email:
        logger.warning("ADMIN_EMAIL not set, skipping Pro request notification")
        return

    admin_notification_enabled = getattr(settings, 'ADMIN_NOTIFICATION_ENABLED', True)
    if not admin_notification_enabled:
        return

    try:
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

        admin_ad_url = (
            f"{site_url}/admin/ads/ad/{ad.id}/"
            if site_url
            else f"/admin/ads/ad/{ad.id}/"
        )
        owner_username = ad.owner.username if ad.owner else 'N/A'
        owner_email = ad.owner.email if ad.owner else 'N/A'
        requested_at = (
            ad.pro_requested_at.strftime('%Y-%m-%d %H:%M')
            if ad.pro_requested_at
            else timezone.now().strftime('%Y-%m-%d %H:%M')
        )

        subject = f"Pro Upgrade Request: {ad.title[:50]}"
        message = f"""
A Pro upgrade has been requested for an ad:

Title: {ad.title}
Ad ID: {ad.id}
Owner: {owner_username}
Owner Email: {owner_email}
Phone: {ad.pro_request_phone or 'N/A'}
Requested At: {requested_at}

Review at: {admin_ad_url}
"""

        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin_email],
            fail_silently=False,
        )

        logger.info(f"Admin notification sent for Pro request on ad: {ad.id}")
    except Exception as e:
        logger.error(
            f"Error sending admin notification for Pro request on ad {ad.id}: {e}",
            exc_info=True,
        )

