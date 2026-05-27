from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.account.signals import email_confirmed, user_signed_up
from allauth.socialaccount.signals import social_account_added, pre_social_login
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.models import Site
from django.conf import settings
from django.urls import reverse
from .models import UserProfile, Post
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create UserProfile when a User is created."""
    if created:
        try:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            # In development (DEBUG=True), auto-verify users to allow immediate login
            # In production, email verification is mandatory and will verify via handle_email_confirmed
            from django.conf import settings
            if settings.DEBUG and not profile.is_site_verified:
                profile.is_site_verified = True
                profile.site_verified_at = timezone.now()
                profile.save()
        except Exception as e:
            # Log error but don't block user creation
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error creating user profile: {e}")


def send_welcome_email_to_user(user):
    """
    Send welcome email once after the user's email is verified.
    Used for email/password signup (via email_confirmed) and new Google signups.
    """
    if not user.email:
        logger.info(
            "Skipping welcome email for user %s: no email address",
            user.username,
        )
        return

    try:
        profile, _ = UserProfile.objects.get_or_create(user=user)

        if profile.welcome_email_sent:
            logger.info(
                "Welcome email already sent to %s, skipping",
                user.email,
            )
            return

        try:
            site = Site.objects.get_current()
            site_domain = site.domain
            if not site_domain.startswith('http'):
                protocol = 'https' if not settings.DEBUG else 'http'
                site_url = f"{protocol}://{site_domain}"
            else:
                site_url = site_domain
        except Exception as e:
            logger.warning(f"Error getting site domain: {e}, using relative URLs")
            site_url = ''

        user_display_name = user.first_name or user.username or user.email.split('@')[0]

        try:
            home_url = f"{site_url}{reverse('home')}" if site_url else reverse('home')
        except Exception:
            home_url = site_url if site_url else '/'

        try:
            member_guide_url = (
                f"{site_url}{reverse('member_guide')}" if site_url else reverse('member_guide')
            )
        except Exception:
            member_guide_url = site_url + '/member-guide/' if site_url else '/member-guide/'

        try:
            complete_setup_url = (
                f"{site_url}{reverse('complete_setup')}"
                if site_url
                else reverse('complete_setup')
            )
        except Exception:
            complete_setup_url = site_url + '/complete-setup/' if site_url else '/complete-setup/'

        subject = (
            "کاربر گرامی، به پلتفرم «پیوند» — "
            "جامعهٔ آنلاین ایرانیان ساکن سوئد — خوش آمدید."
        )
        context = {
            'user': user,
            'user_display_name': user_display_name,
            'site_name': 'پیوند | Peyvand',
            'home_url': home_url,
            'member_guide_url': member_guide_url,
            'complete_setup_url': complete_setup_url,
            'site_url': site_url,
        }

        try:
            text_content = render_to_string('emails/welcome_email.txt', context)
            html_content = render_to_string('emails/welcome_email.html', context)
        except Exception as e:
            logger.error(f"Error rendering welcome email templates: {e}")
            return

        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email],
            )
            msg.attach_alternative(html_content, "text/html")
            msg.send()

            profile.welcome_email_sent = True
            profile.save(update_fields=['welcome_email_sent'])

            logger.info(f"Welcome email sent successfully to {user.email}")

            if settings.DEBUG:
                print(f"[DEBUG] Welcome email sent to: {user.email}")

        except Exception as e:
            logger.error(
                f"Error sending welcome email to {user.email}: {e}",
                exc_info=True,
            )

    except Exception as e:
        logger.error(
            f"Error in send_welcome_email_to_user for {user.username}: {e}",
            exc_info=True,
        )


@receiver(email_confirmed)
def handle_email_confirmed(request, email_address, **kwargs):
    """
    When email is confirmed via email/password signup, treat this as identity
    verification only.

    Site verification (onboarding/terms acceptance) is handled separately via
    the /complete-setup/ flow.
    """
    user = email_address.user
    try:
        UserProfile.objects.get_or_create(user=user)
    except Exception as e:
        logger.error(f"Error updating profile on email confirmation: {e}")

    send_welcome_email_to_user(user)


@receiver(pre_social_login)
def handle_pre_social_login(request, sociallogin, **kwargs):
    """
    Before Google OAuth login completes, ensure email is marked as verified.
    Google emails are trusted, but site verification is still required.
    Also ensure username is set before login completes (so welcome message shows it).
    """
    if sociallogin.account.provider == 'google' and sociallogin.user.email:
        # Ensure username is set BEFORE login completes (so welcome message shows it)
        # Set username on the user object directly (django-allauth will save it)
        # Don't save the user here - let django-allauth handle that
        if not sociallogin.user.username and sociallogin.user.email:
            try:
                # Generate username from email (before @ symbol)
                username_base = sociallogin.user.email.split('@')[0]
                # Sanitize username: remove any invalid characters
                username_base = ''.join(c for c in username_base if c.isalnum() or c in ['_', '-'])
                # Limit username length to 150 characters (Django's max)
                if len(username_base) > 150:
                    username_base = username_base[:150]
                
                # For new users (no pk), check uniqueness to avoid race conditions
                # Use select_for_update if available, otherwise check before setting
                if not sociallogin.user.pk:
                    # Check if username is available, add suffix if needed
                    username = username_base
                    counter = 1
                    # Check uniqueness even for new users to prevent race conditions
                    while User.objects.filter(username=username).exists():
                        suffix = str(counter)
                        max_base_len = 150 - len(suffix) - 1  # -1 for underscore
                        if len(username_base) > max_base_len:
                            username_base = username_base[:max_base_len]
                        username = f"{username_base}_{suffix}"
                        counter += 1
                        # Safety limit to prevent infinite loop
                        if counter > 1000:
                            # Fallback: use timestamp-based username
                            import time
                            username = f"{username_base[:120]}_{int(time.time())}"
                            break
                    sociallogin.user.username = username
                else:
                    # For existing users, ensure uniqueness
                    username = username_base
                    counter = 1
                    while User.objects.filter(username=username).exclude(pk=sociallogin.user.pk).exists():
                        suffix = str(counter)
                        max_base_len = 150 - len(suffix) - 1  # -1 for underscore
                        if len(username_base) > max_base_len:
                            username_base = username_base[:max_base_len]
                        username = f"{username_base}_{suffix}"
                        counter += 1
                        # Safety limit
                        if counter > 1000:
                            import time
                            username = f"{username_base[:120]}_{int(time.time())}"
                            break
                    sociallogin.user.username = username
            except Exception as e:
                # Log error but don't block login - let django-allauth handle it
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error setting username in pre_social_login: {e}", exc_info=True)
        
        # Note: Email verification is handled in social_account_added signal
        # because pre_social_login fires before user is saved to database


@receiver(social_account_added)
def handle_social_account_added(request, sociallogin, **kwargs):
    """
    When a user signs up via Google OAuth:
    - Email is already verified by Google (trusted)
    - In development: auto-verify for immediate access
    - In production: require site-level verification (terms acceptance)
    - Logs auto-connect events when social account is linked to existing user
    """
    user = sociallogin.user
    if sociallogin.account.provider == 'google':
        # Log auto-connect event if this is linking to an existing account
        import logging
        logger = logging.getLogger(__name__)
        if user.pk:  # User already exists (auto-connected)
            logger.info(
                f"Auto-connected Google account for existing user: {user.email} (user_id: {user.pk})",
                extra={'user_id': user.pk, 'email': user.email, 'provider': 'google'}
            )
        # User should already be saved by django-allauth at this point
        # Don't save the user here - it's already saved
        
        # Username should already be set in pre_social_login, but check again as fallback
        if not user.username and user.email and user.pk:
            try:
                # Generate username from email (before @ symbol)
                username_base = user.email.split('@')[0]
                # Sanitize username: remove any invalid characters
                username_base = ''.join(c for c in username_base if c.isalnum() or c in ['_', '-'])
                # Limit to 150 characters
                if len(username_base) > 150:
                    username_base = username_base[:150]
                
                # Ensure username is unique
                username = username_base
                counter = 1
                while User.objects.filter(username=username).exclude(pk=user.pk).exists():
                    suffix = str(counter)
                    max_base_len = 150 - len(suffix) - 1  # -1 for underscore
                    if len(username_base) > max_base_len:
                        username_base = username_base[:max_base_len]
                    username = f"{username_base}_{suffix}"
                    counter += 1
                    # Safety limit to prevent infinite loop
                    if counter > 1000:
                        import time
                        username = f"{username_base[:120]}_{int(time.time())}"
                        break
                user.username = username
                user.save(update_fields=['username'])
            except Exception as e:
                # Log error but don't block signup
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error setting username in social_account_added: {e}", exc_info=True)
        
        # Google emails are verified, so mark email as verified
        if user.email and user.pk:
            from allauth.account.models import EmailAddress
            try:
                email_address, created = EmailAddress.objects.get_or_create(
                    user=user,
                    email=user.email,
                    defaults={'verified': True, 'primary': True}
                )
                if not created:
                    email_address.verified = True
                    email_address.primary = True
                    email_address.save()
            except Exception as e:
                # Log error but don't block signup
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error setting email address for social login: {e}")
        
        # Ensure UserProfile exists (create if it doesn't)
        if user.pk:
            try:
                profile, created = UserProfile.objects.get_or_create(user=user)
                
                # In development, auto-verify users for immediate access
                # In production, require site verification (terms acceptance)
                from django.conf import settings
                if settings.DEBUG:
                    # Auto-verify in development
                    if not profile.is_site_verified:
                        profile.is_site_verified = True
                        profile.site_verified_at = timezone.now()
                        profile.save()
                # In production, is_site_verified remains False until user completes setup
            except Exception as e:
                # Log error but don't block signup
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error creating/updating profile for social login: {e}")

            # New Google signups: email is provider-verified; send welcome once here.
            if user.pk and not sociallogin.is_existing:
                send_welcome_email_to_user(user)


# Admin Notification Signals
@receiver(post_save, sender=Post)
def notify_admin_new_post(sender, instance, created, **kwargs):
    """Send email to admin when new draft post is created."""
    if not created:
        return  # Only on creation
    
    # Only notify for drafts (status=0)
    if instance.status != 0:
        return
    
    # Check if notifications are enabled
    admin_email = getattr(settings, 'ADMIN_EMAIL', None)
    if not admin_email:
        logger.warning("ADMIN_EMAIL not set, skipping post notification")
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
        
        admin_post_url = f"{site_url}/admin/blog/post/{instance.id}/" if site_url else f"/admin/blog/post/{instance.id}/"
        
        subject = f"New Post Draft: {instance.title[:50]}"
        message = f"""
A new post draft has been submitted:

Title: {instance.title}
Author: {instance.author.username}
Category: {instance.category.name if instance.category else 'None'}
Created: {instance.created_on.strftime('%Y-%m-%d %H:%M')}

Review at: {admin_post_url}
"""
        
        from django.core.mail import send_mail
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [admin_email],
            fail_silently=False,
        )
        
        logger.info(f"Admin notification sent for new post draft: {instance.id}")
    except Exception as e:
        logger.error(f"Error sending admin notification for new post: {e}", exc_info=True)
