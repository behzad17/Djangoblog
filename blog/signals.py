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
        UserProfile.objects.get_or_create(user=instance)


@receiver(email_confirmed)
def handle_email_confirmed(request, email_address, **kwargs):
    """
    When email is confirmed via email/password signup, mark as site verified.
    For email/password signups, email verification IS the site verification.
    """
    user = email_address.user
    if hasattr(user, 'profile'):
        if not user.profile.is_site_verified:
            user.profile.is_site_verified = True
            user.profile.site_verified_at = timezone.now()
            user.profile.save()


@receiver(pre_social_login)
def handle_pre_social_login(request, sociallogin, **kwargs):
    """
    Before Google OAuth login completes, ensure email is marked as verified.
    Google emails are trusted, but site verification is still required.
    """
    if sociallogin.account.provider == 'google' and sociallogin.user.email:
        from allauth.account.models import EmailAddress
        email_address, created = EmailAddress.objects.get_or_create(
            user=sociallogin.user,
            email=sociallogin.user.email,
            defaults={'verified': True, 'primary': True}
        )
        if not created:
            email_address.verified = True
            email_address.primary = True
            email_address.save()


@receiver(social_account_added)
def handle_social_account_added(request, sociallogin, **kwargs):
    """
    When a user signs up via Google OAuth:
    - Email is already verified by Google (trusted)
    - But we still require site-level verification (terms acceptance)
    - Set email as verified, but leave is_site_verified=False
    """
    user = sociallogin.user
    if sociallogin.account.provider == 'google':
        # Google emails are verified, so mark email as verified
        if user.email:
            from allauth.account.models import EmailAddress
            email_address, created = EmailAddress.objects.get_or_create(
                user=user,
                email=user.email,
                defaults={'verified': True, 'primary': True}
            )
            if not created:
                email_address.verified = True
                email_address.primary = True
                email_address.save()
        
        # But don't mark as site_verified yet - user must complete setup
        # is_site_verified remains False until user completes setup
