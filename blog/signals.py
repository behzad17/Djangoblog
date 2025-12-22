from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from allauth.account.signals import email_confirmed, user_signed_up
from allauth.socialaccount.signals import social_account_added, pre_social_login
from django.utils import timezone
from .models import UserProfile


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


@receiver(email_confirmed)
def handle_email_confirmed(request, email_address, **kwargs):
    """
    When email is confirmed via email/password signup, mark as site verified.
    For email/password signups, email verification IS the site verification.
    """
    user = email_address.user
    try:
        # Ensure UserProfile exists (create if it doesn't)
        profile, _ = UserProfile.objects.get_or_create(user=user)
        if not profile.is_site_verified:
            profile.is_site_verified = True
            profile.site_verified_at = timezone.now()
            profile.save()
    except Exception as e:
        # Log error but don't block email confirmation
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating profile on email confirmation: {e}")


@receiver(pre_social_login)
def handle_pre_social_login(request, sociallogin, **kwargs):
    """
    Before Google OAuth login completes, ensure email is marked as verified.
    Google emails are trusted, but site verification is still required.
    """
    if sociallogin.account.provider == 'google' and sociallogin.user.email:
        # Ensure user is saved before accessing related objects
        if not sociallogin.user.pk:
            sociallogin.user.save()
        
        from allauth.account.models import EmailAddress
        try:
            email_address, created = EmailAddress.objects.get_or_create(
                user=sociallogin.user,
                email=sociallogin.user.email,
                defaults={'verified': True, 'primary': True}
            )
            if not created:
                email_address.verified = True
                email_address.primary = True
                email_address.save()
        except Exception as e:
            # Log error but don't block login
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error setting email address in pre_social_login: {e}")


@receiver(social_account_added)
def handle_social_account_added(request, sociallogin, **kwargs):
    """
    When a user signs up via Google OAuth:
    - Email is already verified by Google (trusted)
    - In development: auto-verify for immediate access
    - In production: require site-level verification (terms acceptance)
    """
    user = sociallogin.user
    if sociallogin.account.provider == 'google':
        # Ensure user is saved first (needed for checking username uniqueness)
        if not user.pk:
            user.save()
        
        # Ensure username is set (use email prefix if username is empty)
        if not user.username and user.email:
            # Generate username from email (before @ symbol)
            username_base = user.email.split('@')[0]
            # Ensure username is unique
            username = username_base
            counter = 1
            while User.objects.filter(username=username).exclude(pk=user.pk).exists():
                username = f"{username_base}{counter}"
                counter += 1
            user.username = username
            user.save()
        
        # Google emails are verified, so mark email as verified
        if user.email:
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
